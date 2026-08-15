#!/usr/bin/env python3
"""Generate the controlled four-topic benchmark outcome figure.

The figure is derived only from the frozen benchmark SQLite snapshot in the
nested results repository. It uses the manifest's four sequential topic
windows and keeps completed, failed, and awaiting-review outcomes distinct.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
DB_PATH = RESULTS / "data" / "conceptcast.db"
OUT = RESULTS / "figures" / "fig5_5_controlled_benchmark_outcomes.png"

WINDOWS = [
    ("Backpropagation", "2026-08-14 21:38:42", "2026-08-14 23:07:43"),
    ("Fourier transform", "2026-08-14 23:07:44", "2026-08-15 00:55:46"),
    ("Doppler effect", "2026-08-15 00:55:47", "2026-08-15 03:06:04"),
    ("Eigenvectors", "2026-08-15 03:06:05", "2026-08-15 04:28:48"),
]


def load_counts() -> dict[str, Counter[str]]:
    conn = sqlite3.connect(DB_PATH)
    try:
        counts: dict[str, Counter[str]] = {}
        for label, start, end in WINDOWS:
            rows = conn.execute(
                "SELECT status, validation FROM jobs "
                "WHERE created_at >= ? AND created_at <= ?",
                (start, end),
            ).fetchall()
            if len(rows) != 9:
                raise RuntimeError(f"{label}: expected 9 jobs, found {len(rows)}")
            counter: Counter[str] = Counter()
            for status, validation in rows:
                if status == "completed":
                    counter["Completed"] += 1
                elif status == "awaiting_review":
                    counter["Awaiting review"] += 1
                elif status == "failed":
                    counter["Failed"] += 1
                else:
                    raise RuntimeError(f"{label}: unexpected terminal status {status!r}")
            counts[label] = counter
        if sum(sum(c.values()) for c in counts.values()) != 36:
            raise RuntimeError("controlled cohort does not contain exactly 36 jobs")
        return counts
    finally:
        conn.close()


def main() -> None:
    counts = load_counts()
    labels = list(counts)
    categories = ["Completed", "Failed", "Awaiting review"]
    colors = ["#4daf4a", "#e41a1c", "#ff7f00"]
    bottoms = [0] * len(labels)

    fig, ax = plt.subplots(figsize=(8.5, 4.8), constrained_layout=True)
    for category, color in zip(categories, colors):
        values = [counts[label][category] for label in labels]
        ax.bar(labels, values, bottom=bottoms, label=category, color=color)
        bottoms = [b + v for b, v in zip(bottoms, values)]

    ax.set_ylim(0, 9)
    ax.set_ylabel("Jobs (out of 9 models)")
    ax.set_title("Controlled Four-Topic Benchmark Outcomes")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.16))
    fig.savefig(OUT, dpi=220, bbox_inches="tight")
    print(json.dumps({"output": str(OUT), "counts": {k: dict(v) for k, v in counts.items()}}))


if __name__ == "__main__":
    main()
