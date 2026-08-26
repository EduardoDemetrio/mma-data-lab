from __future__ import annotations

from pathlib import Path

from padronizacao_utils import print_summary, read_csv_auto, save_tables, standardize_dataframe


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "raw" / "Ultimate UFC Dataset"
BRONZE_DIR = BASE_DIR / "processed_bronze" / "ultimate_ufc_dataset"
REPORT_PATH = BASE_DIR / "docs" / "qualidade_bronze_ultimate_ufc_dataset.csv"


FILES = {
    "ufc_master": RAW_DIR / "ufc-master.csv",
    "upcoming": RAW_DIR / "upcoming.csv",
}


def main() -> None:
    tables = {}
    for table_name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
        tables[table_name] = standardize_dataframe(read_csv_auto(path))

    save_tables(tables, BRONZE_DIR, REPORT_PATH)
    print_summary("Ultimate UFC Dataset", RAW_DIR, BRONZE_DIR, tables)


if __name__ == "__main__":
    main()
