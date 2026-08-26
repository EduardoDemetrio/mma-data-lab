from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from padronizacao_utils import print_summary, read_csv_auto, save_tables, standardize_dataframe


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "raw" / "repos_investigacao" / "ultimate_ufc_dataset"
BRONZE_DIR = BASE_DIR / "processed_bronze" / "ultimate_ufc_dataset_repo"
REPORT_PATH = BASE_DIR / "docs" / "qualidade_bronze_ultimate_ufc_dataset_repo.csv"


FILES = {
    "ufc_master": RAW_DIR / "ufc-master.csv",
    "upcoming": RAW_DIR / "upcoming.csv",
    "data_ultimate_ufc_dataset_ufc_master": RAW_DIR
    / "data"
    / "ultimate_ufc_dataset"
    / "ufc-master.csv",
    "data_ultimate_ufc_dataset_upcoming": RAW_DIR
    / "data"
    / "ultimate_ufc_dataset"
    / "upcoming.csv",
    "kaggle_ufc_master": RAW_DIR / "data" / "load_to_github_and_kaggle" / "ufc-master.csv",
    "kaggle_upcoming": RAW_DIR / "data" / "load_to_github_and_kaggle" / "upcoming.csv",
    "dataset_metadata": RAW_DIR / "data" / "load_to_github_and_kaggle" / "dataset-metadata.json",
}


def load_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as file:
            return pd.json_normalize(json.load(file))
    return read_csv_auto(path)


def main() -> None:
    tables = {}
    for table_name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
        tables[table_name] = standardize_dataframe(load_table(path))

    save_tables(tables, BRONZE_DIR, REPORT_PATH)
    print_summary("ultimate_ufc_dataset repo", RAW_DIR, BRONZE_DIR, tables)


if __name__ == "__main__":
    main()
