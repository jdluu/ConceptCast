"""SSE event streaming routes for real-time job status updates.

Provides the `/events` endpoint that delivers job state changes to the
frontend via Server-Sent Events, using Redis pub/sub notifications.
"""

import asyncio
import json
import time
from collections.abc import AsyncGenerator, Callable
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas import CurriculumPlan
from infra.database import AsyncSessionLocal
from infra.models.job import JobRecord
from services.jobs.events import job_event_manager
from services.jobs.serialization import map_job_record_to_status

logger = structlog.get_logger(__name__)

router = APIRouter()


async def _stream_job_events(
    job_id: str, db_session_factory: Callable[[], AsyncSession]
) -> AsyncGenerator[str, None]:
    """Generates Server-Sent Events (SSE) for a specific job by polling the database.

    Args:
        job_id: The unique identifier of the job to monitor.
        db_session_factory: Factory function for creating database sessions.

    Yields:
        SSE events as strings formatted for the client.
    """
    last_status = None
    last_step = None
    last_thought_count = 0
    last_thought_content_len = 0
    last_artifact_state: tuple[bool, bool, bool, bool, bool, int] | None = None
    first_emit = True
    last_emit_monotonic = 0.0
    min_emit_interval_seconds = 0.35

    while True:
        async with db_session_factory() as db:
            result = await db.execute(
                select(JobRecord)
                .options(selectinload(JobRecord.thoughts))
                .where(JobRecord.job_id == job_id)
            )
            job = result.scalar_one_or_none()

            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            thoughts = job.thoughts or []
            current_thought_content_len = len(thoughts[-1].content) if thoughts else 0

            status_changed = job.status != last_status
            step_changed = job.current_step != last_step
            thought_count_changed = len(thoughts) != last_thought_count
            thought_content_changed = (
                current_thought_content_len != last_thought_content_len
            )
            artifact_state = (
                job.plan is not None,
                CurriculumPlan.model_validate(job.plan).is_structurally_valid()[0]
                if job.plan
                else False,
                job.storyboard is not None,
                bool(job.manim_code),
                bool(job.error),
                int(job.render_progress or 0),
            )
            artifact_changed = artifact_state != last_artifact_state

            should_emit = (
                first_emit
                or status_changed
                or step_changed
                or artifact_changed
                or thought_count_changed
                or thought_content_changed
            )

            # Throttle noisy high-frequency thought-content-only updates.
            now_monotonic = time.monotonic()
            only_content_delta = (
                not first_emit
                and not status_changed
                and not step_changed
                and not artifact_changed
                and not thought_count_changed
                and thought_content_changed
            )
            if only_content_delta and (
                now_monotonic - last_emit_monotonic < min_emit_interval_seconds
            ):
                should_emit = False

            if should_emit:
                status_payload = map_job_record_to_status(job)
                yield f"data: {status_payload.model_dump_json()}\n\n"
                last_status = job.status
                last_step = job.current_step
                last_thought_count = len(thoughts)
                last_thought_content_len = current_thought_content_len
                last_artifact_state = artifact_state
                first_emit = False
                last_emit_monotonic = now_monotonic

            if job.status in ["completed", "failed"]:
                break

        await job_event_manager.wait_for_update(job_id, timeout=15.0)


@router.get("/{job_id}/events")
async def job_events(
    job_id: str,
    db_session_factory: Annotated[
        Callable[[], AsyncSession], Depends(lambda: AsyncSessionLocal)
    ],
) -> StreamingResponse:
    """Provides a real-time stream of job updates via Server-Sent Events (SSE).

    Args:
        job_id: The unique identifier of the job to stream.
        db_session_factory: Dependency for creating database sessions.

    Returns:
        StreamingResponse: An SSE event stream.
    """
    return StreamingResponse(
        _stream_job_events(job_id, db_session_factory), media_type="text/event-stream"
    )


async def _ws_send_loop(
    websocket: WebSocket,
    job_id: str,
    db_session_factory: Callable[[], AsyncSession],
) -> None:
    """Handles sending real-time job status changes over the WebSocket connection."""
    last_status = None
    last_step = None
    last_thought_count = 0
    last_thought_content_len = 0
    last_artifact_state: tuple[bool, bool, bool, bool, bool, int] | None = None
    first_emit = True
    last_emit_monotonic = 0.0
    min_emit_interval_seconds = 0.35

    try:
        while True:
            async with db_session_factory() as db:
                result = await db.execute(
                    select(JobRecord)
                    .options(selectinload(JobRecord.thoughts))
                    .where(JobRecord.job_id == job_id)
                )
                job = result.scalar_one_or_none()

                if not job:
                    await websocket.send_json({"error": "Job not found"})
                    break

                thoughts = job.thoughts or []
                current_thought_content_len = (
                    len(thoughts[-1].content) if thoughts else 0
                )

                status_changed = job.status != last_status
                step_changed = job.current_step != last_step
                thought_count_changed = len(thoughts) != last_thought_count
                thought_content_changed = (
                    current_thought_content_len != last_thought_content_len
                )
                artifact_state = (
                    job.plan is not None,
                    CurriculumPlan.model_validate(job.plan).is_structurally_valid()[0]
                    if job.plan
                    else False,
                    job.storyboard is not None,
                    bool(job.manim_code),
                    bool(job.error),
                    int(job.render_progress or 0),
                )
                artifact_changed = artifact_state != last_artifact_state

                should_emit = (
                    first_emit
                    or status_changed
                    or step_changed
                    or artifact_changed
                    or thought_count_changed
                    or thought_content_changed
                )

                # Throttle noisy high-frequency thought-content-only updates.
                now_monotonic = time.monotonic()
                only_content_delta = (
                    not first_emit
                    and not status_changed
                    and not step_changed
                    and not artifact_changed
                    and not thought_count_changed
                    and thought_content_changed
                )
                if only_content_delta and (
                    now_monotonic - last_emit_monotonic < min_emit_interval_seconds
                ):
                    should_emit = False

                if should_emit:
                    status_payload = map_job_record_to_status(job)
                    await websocket.send_text(status_payload.model_dump_json())
                    last_status = job.status
                    last_step = job.current_step
                    last_thought_count = len(thoughts)
                    last_thought_content_len = current_thought_content_len
                    last_artifact_state = artifact_state
                    first_emit = False
                    last_emit_monotonic = now_monotonic

                if job.status in ["completed", "failed"]:
                    break

            await job_event_manager.wait_for_update(job_id, timeout=15.0)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("websocket_send_error", job_id=job_id, error=str(e))


async def _ws_receive_loop(
    websocket: WebSocket,
    job_id: str,
    db_session_factory: Callable[[], AsyncSession],
) -> None:
    """Handles receiving control commands (such as cancellation) over the WebSocket connection."""
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue

            action = payload.get("action")
            if action == "cancel":
                async with db_session_factory() as db:
                    from services.jobs.manager import update_job_status

                    await update_job_status(
                        job_id,
                        {
                            "status": "failed",
                            "current_step": "cancelled_by_user",
                            "error": "Job cancelled by user",
                        },
                        db,
                    )
                    await db.commit()
                logger.info("job_cancelled_via_websocket", job_id=job_id)
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("websocket_receive_error", job_id=job_id, error=str(e))


async def _ws_ping_loop(websocket: WebSocket) -> None:
    """Sends periodic heartbeats to prevent connection drop by proxy servers.

    Args:
        websocket: The active WebSocket connection.
    """
    try:
        while True:
            await asyncio.sleep(25.0)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug("websocket_ping_error", error=str(e))


@router.websocket("/{job_id}/control")
async def job_control_ws(
    websocket: WebSocket,
    job_id: str,
    db_session_factory: Annotated[
        Callable[[], AsyncSession], Depends(lambda: AsyncSessionLocal)
    ],
) -> None:
    """Provides a bi-directional WebSocket control channel for a specific job.

    Streams real-time updates (status, progress, thoughts) to the frontend,
    and listens for control frames (e.g. cancellation) from the frontend.

    Args:
        websocket: The active WebSocket connection.
        job_id: The unique identifier of the job to monitor/control.
        db_session_factory: Dependency for creating database sessions.
    """
    await websocket.accept()
    logger.info("websocket_connected", job_id=job_id)

    # Run all loops concurrently. If send_task or receive_task finishes, cancel the others.
    send_task = asyncio.create_task(
        _ws_send_loop(websocket, job_id, db_session_factory)
    )
    receive_task = asyncio.create_task(
        _ws_receive_loop(websocket, job_id, db_session_factory)
    )
    ping_task = asyncio.create_task(_ws_ping_loop(websocket))

    try:
        # Wait for either sender or receiver to finish (ping loop is purely helper and shouldn't trigger completion)
        await asyncio.wait(
            [send_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
    finally:
        for task in [send_task, receive_task, ping_task]:
            if not task.done():
                task.cancel()
        import contextlib

        with contextlib.suppress(Exception):
            await websocket.close()
        logger.info("websocket_connection_closed", job_id=job_id)
