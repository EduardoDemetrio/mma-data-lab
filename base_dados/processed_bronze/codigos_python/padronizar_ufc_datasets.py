from __future__ import annotations

from pathlib import Path

from padronizacao_utils import print_summary, read_csv_auto, save_tables, standardize_dataframe


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "raw" / "UFC DATASETS"
BRONZE_DIR = BASE_DIR / "processed_bronze" / "ufc_datasets"
REPORT_PATH = BASE_DIR / "docs" / "qualidade_bronze_ufc_datasets.csv"


FILES = {
    "ufc": RAW_DIR / "UFC.csv",
    "event_details": RAW_DIR / "event_details.csv",
    "fight_details": RAW_DIR / "fight_details.csv",
    "fighter_details": RAW_DIR / "fighter_details.csv",
}


def main() -> None:
    tables = {}
    for table_name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
        tables[table_name] = standardize_dataframe(read_csv_auto(path))

    save_tables(tables, BRONZE_DIR, REPORT_PATH)
    print_summary("UFC DATASETS", RAW_DIR, BRONZE_DIR, tables)


if __name__ == "__main__":
    main()
