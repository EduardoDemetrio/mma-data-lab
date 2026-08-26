from __future__ import annotations

import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


SCRIPTS = [
    "padronizar_scrape_ufc_stats.py",
    "padronizar_ufc_datalab.py",
    "padronizar_ufc_stats_crawler.py",
    "padronizar_ultimate_ufc_dataset_repo.py",
    "padronizar_ufc_datasets.py",
    "padronizar_ufc_fight_historical.py",
    "padronizar_ultimate_ufc_dataset.py",
]


def main() -> None:
    for script in SCRIPTS:
        script_path = BASE_DIR / script
        print("\n" + "=" * 80)
        print(f"Rodando {script}")
        print("=" * 80)
        subprocess.run([sys.executable, str(script_path)], check=True)

    print("\nTodas as padronizacoes foram concluidas.")


if __name__ == "__main__":
    main()
