from __future__ import annotations

from pathlib import Path

from padronizacao_utils import print_summary, read_csv_auto, save_tables, standardize_dataframe


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "raw" / "UFC Fight historical"
BRONZE_DIR = BASE_DIR / "processed_bronze" / "ufc_fight_historical"
REPORT_PATH = BASE_DIR / "docs" / "qualidade_bronze_ufc_fight_historical.csv"


FILES = {
    "data": RAW_DIR / "data.csv",
    "preprocessed_data": RAW_DIR / "preprocessed_data.csv",
    "raw_fighter_details": RAW_DIR / "raw_fighter_details.csv",
    "raw_total_fight_data": RAW_DIR / "raw_total_fight_data.csv",
}


def main() -> None:
    tables = {}
    for table_name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
        tables[table_name] = standardize_dataframe(read_csv_auto(path))

    save_tables(tables, BRONZE_DIR, REPORT_PATH)
    print_summary("UFC Fight historical", RAW_DIR, BRONZE_DIR, tables)


if __name__ == "__main__":
    main()
