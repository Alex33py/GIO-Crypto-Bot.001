#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Backup Script - Day 3 Completion
Creates backup of critical files and results
"""

import os
import shutil
from datetime import datetime
import json


def main():
    # Создать timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/backup_{timestamp}"

    # Создать структуру
    os.makedirs(backup_dir, exist_ok=True)

    # Файлы для бэкапа
    critical_files = [
        "data/scenarios/gio_scenarios_112_final_v3.json",
        "core/scenario_matcher.py",
        "tests/backtest_full_simulation.py",
        "tests/market_data_simulator.py",
        "analytics/mtf_flexible_scorer.py",
        "tests/analyze_false_signals.py",
    ]

    # Папки для бэкапа
    critical_dirs = [
        "tests/results/",
        "data/scenarios/",
    ]

    print("=" * 70)
    print("💾 BACKUP PROJECT - DAY 3 COMPLETE")
    print("=" * 70)

    # Бэкап файлов
    backed_up_files = 0
    for file_path in critical_files:
        if os.path.exists(file_path):
            dest = os.path.join(backup_dir, os.path.dirname(file_path))
            os.makedirs(dest, exist_ok=True)
            shutil.copy2(file_path, dest)
            print(f"✅ Backed up: {file_path}")
            backed_up_files += 1
        else:
            print(f"⚠️  Not found: {file_path}")

    # Бэкап папок
    backed_up_dirs = 0
    for dir_path in critical_dirs:
        if os.path.exists(dir_path):
            dest = os.path.join(backup_dir, dir_path)
            shutil.copytree(dir_path, dest, dirs_exist_ok=True)
            file_count = sum(1 for _, _, files in os.walk(dir_path) for f in files)
            print(f"✅ Backed up: {dir_path} ({file_count} files)")
            backed_up_dirs += 1
        else:
            print(f"⚠️  Not found: {dir_path}")

    # Создать манифест
    manifest = {
        "timestamp": timestamp,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S EET"),
        "day": 3,
        "status": "100% COMPLETE",
        "milestone": "Day 1-3: Foundation + Testing + Fixes",
        "achievements": {
            "mtf_status": "STRONG (activated)",
            "scenarios_total": 112,
            "scenarios_merged": "100 v3 + 12 v2",
            "backtest_completed": True,
            "case_sensitivity_fixed": True,
        },
        "backtest_results": {
            "win_rate": 30.0,
            "profit_factor": 1.38,
            "scenarios_used": 31,
            "total_trades": 10,
            "avg_score": 75.0,
        },
        "files_backed_up": backed_up_files,
        "dirs_backed_up": backed_up_dirs,
    }

    manifest_path = os.path.join(backup_dir, "MANIFEST.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Расчет размера
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(backup_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)

    print(f"\n{'=' * 70}")
    print(f"✅ Backup complete!")
    print(f"📁 Location: {backup_dir}")
    print(f"📦 Total size: {total_size / 1024 / 1024:.2f} MB")
    print(f"📄 Files backed up: {backed_up_files}")
    print(f"📂 Directories backed up: {backed_up_dirs}")
    print(f"📋 Manifest: {manifest_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
