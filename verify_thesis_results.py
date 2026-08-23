#!/usr/bin/env python3
"""ConceptCast Thesis Results Verification Script.

This script queries the SQLite database (data/conceptcast.db) to extract
and print the exact metrics, success rates, and LaTeX tables presented
in the thesis results chapter. Run this script to verify the empirical data.

IMPORTANT — WHICH VERIFIER TO USE:
  This script reads the LIVE database, which keeps growing after the thesis
  benchmarks were frozen. Its output will NOT match published thesis tables.
  To reproduce the numbers printed in the thesis, use the frozen-snapshot
  verifiers in the results repository instead:

      python3 results/verify_table51_historical.py    # Table 5.1 (frozen snapshot 5f4f7f5)
      python3 results/verify_controlled_benchmark.py  # Tables 5.5/5.6 (frozen snapshot 386a271)

  Use this script only to inspect current live-system statistics.
"""

import sqlite3
import re
from collections import defaultdict
from pathlib import Path

# Resolve database path
ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "data" / "conceptcast.db"


def verify_database_metrics():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Map job_ids to models
    c.execute("SELECT job_id, model_id, cost, total_execution_time, status FROM jobs")
    jobs = c.fetchall()
    job_models = {}
    job_metrics = {}
    job_status = {}
    for job_id, model_id, cost, duration, status in jobs:
        job_models[job_id] = model_id
        job_metrics[job_id] = {"cost": cost or 0.0, "duration": duration or 0.0}
        job_status[job_id] = status

    # 2. Extract scene-level syntax attempts
    c.execute("SELECT job_id, content FROM thoughts WHERE phase IN ('Syntax Check', 'Progress') ORDER BY ts ASC")
    thoughts = c.fetchall()

    model_scene_stats = defaultdict(lambda: defaultdict(list))
    for job_id, content in thoughts:
        model_id = job_models.get(job_id)
        if not model_id:
            continue
        fail_match = re.search(r"Scene\s+(\d+)\s+Failed", content)
        approved_match = re.search(r"Scene\s+(\d+)\s+approved", content)
        
        if fail_match:
            scene_id = int(fail_match.group(1))
            model_scene_stats[model_id][(job_id, scene_id)].append("fail")
        elif approved_match:
            scene_id = int(approved_match.group(1))
            model_scene_stats[model_id][(job_id, scene_id)].append("success")

    print("\n" + "="*80)
    print("1. MODEL-LEVEL SCENE COMPILATION AND REPAIR METRICS (Table 5.1)")
    print("="*80)
    print(r"\begin{table}[htbp]")
    print(r"\centering")
    print(r"\caption{Model-Level Code Compilation and Scene Repair Success Rates}")
    print(r"\label{tab:compilation_success}")
    print(r"\begin{spacing}{1.2}")
    print(r"\begin{tabular}{lccc}")
    print(r"\hline")
    print(r"\textbf{Model ID} & \textbf{Total Scenes} & \textbf{First-Pass Success (\%)} & \textbf{AST Diff Repair Success (\%)} \\")
    print(r"\hline")

    total_scenes_all = 0
    total_first_pass_all = 0
    total_post_repair_all = 0

    model_mapping = {
        "deepseek/deepseek-v4-flash:thinking": "ds-v4-flash",
        "deepseek/deepseek-v4-pro:thinking": "ds-v4-pro",
        "google/gemma-4-31b-it:thinking": "gemma-4-it",
        "minimax/minimax-m2.7": "minimax-m2.7",
        "moonshotai/kimi-k2.6:thinking": "kimi-k2.6",
        "openai/gpt-oss-120b": "gpt-oss-120b",
        "openai/gpt-oss-20b": "gpt-oss-20b",
        "qwen/qwen3.5-122b-a10b:thinking": "qwen-3.5-122b",
        "zai-org/glm-5.1:thinking": "glm-5.1"
    }

    for model_id, scenes in sorted(model_scene_stats.items()):
        total = len(scenes)
        if total == 0:
            continue
        first_pass = 0
        post_repair = 0
        for key, outcomes in scenes.items():
            if "fail" not in outcomes:
                first_pass += 1
                post_repair += 1
            elif "success" in outcomes:
                post_repair += 1
        
        total_scenes_all += total
        total_first_pass_all += first_pass
        total_post_repair_all += post_repair

        tex_model_id = model_mapping.get(model_id, model_id)
        print(f"\\texttt{{{tex_model_id:<15}}} & {total:<12} & {first_pass/total*100:<25.1f} & {post_repair/total*100:<28.1f} \\\\")

    weighted_first_pass = (total_first_pass_all / total_scenes_all) * 100
    weighted_post_repair = (total_post_repair_all / total_scenes_all) * 100

    print(r"\hline")
    print(f"\\textbf{{Weighted Mean}} & \\textbf{{{total_scenes_all}}} & \\textbf{{{weighted_first_pass:.1f}}} & \\textbf{{{weighted_post_repair:.1f}}} \\\\")
    print(r"\hline")
    print(r"\end{tabular}")
    print(r"\end{spacing}")
    print(r"\end{table}")

    # 3. Model run performance metrics (duration, cost, completed)
    print("\n" + "="*80)
    print("2. MODEL RENDERING PERFORMANCE AND COSTS")
    print("="*80)
    print("| %-20s | %-12s | %-12s | %-16s | %-12s |" % ("Model ID", "Total Runs", "Completed", "Avg Duration (s)", "Avg Cost ($)"))
    print("|----------------------|--------------|--------------|------------------|--------------|")
    
    model_jobs = defaultdict(list)
    for job_id, model_id in job_models.items():
        model_jobs[model_id].append(job_id)

    for model_id, job_ids in sorted(model_jobs.items()):
        total_runs = len(job_ids)
        completed_runs = sum(1 for j in job_ids if job_status[j] == 'completed')
        
        valid_durations = [job_metrics[j]["duration"] for j in job_ids if job_status[j] == 'completed' and job_metrics[j]["duration"] > 0]
        valid_costs = [job_metrics[j]["cost"] for j in job_ids if job_metrics[j]["cost"] > 0]
        
        avg_duration = sum(valid_durations) / len(valid_durations) if valid_durations else 0.0
        avg_cost = sum(valid_costs) / len(valid_costs) if valid_costs else 0.0
        
        display_name = model_mapping.get(model_id, model_id.split("/")[-1])
        print("| %-20s | %-12d | %-12d | %-16.1f | %-12.4f |" % (display_name, total_runs, completed_runs, avg_duration, avg_cost))

    conn.close()


if __name__ == "__main__":
    verify_database_metrics()
