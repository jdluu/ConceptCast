"""Regression tests for leaked Manim containers.

Killing the ``podman run`` client (the old timeout path) detaches the container:
``--rm`` never fires, so renders stayed ``Up`` for days at 0% CPU. Cleanup must
therefore target the container ID captured via ``--cidfile`` rather than the
client process.
"""

import asyncio
import subprocess
from pathlib import Path

import pytest

from infra.engines.sandbox import MANIM_IMAGE, LocalSandbox


@pytest.fixture
def sandbox() -> LocalSandbox:
    """A sandbox pinned to a container tool, skipping the podman health probe."""
    instance = LocalSandbox()
    instance.container_tool = "docker"
    return instance


def test_base_cmd_records_cidfile(sandbox: LocalSandbox, tmp_path: Path) -> None:
    """The container command must record its ID so it can be reaped later."""
    cidfile = tmp_path / ".manim-cid-abc"
    cmd = sandbox._get_base_cmd(tmp_path, cidfile)

    assert "--rm" in cmd
    assert "--cidfile" in cmd
    assert str(cidfile.absolute()) in cmd
    assert cmd[-1] == MANIM_IMAGE


def test_base_cmd_without_cidfile(sandbox: LocalSandbox, tmp_path: Path) -> None:
    """Omitting the cidfile keeps the previous command shape."""
    assert "--cidfile" not in sandbox._get_base_cmd(tmp_path)


def test_reap_container_removes_by_id(
    sandbox: LocalSandbox,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A recorded container ID is force-removed and the cidfile cleaned up."""
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    cidfile = tmp_path / ".manim-cid-abc"
    cidfile.write_text("deadbeef\n")

    assert sandbox._reap_container(cidfile) is True
    assert calls == [["docker", "rm", "-f", "-t", "2", "deadbeef"]]
    assert not cidfile.exists()


def test_reap_container_is_noop_without_cidfile(
    sandbox: LocalSandbox,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The normal `--rm` path leaves no cidfile and must not shell out."""

    def boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("must not shell out when there is no cidfile")

    monkeypatch.setattr(subprocess, "run", boom)

    assert sandbox._reap_container(tmp_path / "missing") is False


def test_reap_orphans_removes_each(
    sandbox: LocalSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every container for the Manim image is removed, and the count returned."""
    removed: list[str] = []

    def fake_run(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if cmd[1] == "ps":
            return subprocess.CompletedProcess(cmd, 0, "aaa\nbbb\n", "")
        removed.append(cmd[-1])
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert sandbox.reap_orphans() == 2
    assert removed == ["aaa", "bbb"]


def test_terminate_kills_client_and_reaps_container(
    sandbox: LocalSandbox,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The timeout path must reap the container, not just kill the client."""
    reaped: list[Path] = []

    def fake_reap(cidfile: Path) -> bool:
        reaped.append(cidfile)
        return True

    monkeypatch.setattr(sandbox, "_reap_container", fake_reap)
    cidfile = tmp_path / ".manim-cid-abc"

    async def scenario() -> int | None:
        process = await asyncio.create_subprocess_exec("sleep", "30")
        await sandbox._terminate(process, cidfile)
        return process.returncode

    returncode = asyncio.run(scenario())

    assert reaped == [cidfile]
    assert returncode is not None
