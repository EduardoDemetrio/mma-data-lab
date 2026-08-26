from __future__ import annotations

from pathlib import Path

from padronizacao_utils import print_summary, read_csv_auto, save_tables, standardize_dataframe


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "raw" / "repos_investigacao" / "UFC-DataLab"
BRONZE_DIR = BASE_DIR / "processed_bronze" / "ufc_datalab"
REPORT_PATH = BASE_DIR / "docs" / "qualidade_bronze_ufc_datalab.csv"


FILES = {
    "raw_fighter_details": RAW_DIR / "data" / "external_data" / "raw_fighter_details.csv",
    "stats_raw": RAW_DIR / "data" / "stats" / "stats_raw.csv",
    "stats_processed": RAW_DIR / "data" / "stats" / "stats_processed.csv",
    "stats_processed_all_bouts": RAW_DIR / "data" / "stats" / "stats_processed_all_bouts.csv",
    "merged_stats_n_scorecards": RAW_DIR
    / "data"
    / "merged_stats_n_scorecards"
    / "merged_stats_n_scorecards.csv",
    "scorecards": RAW_DIR / "data" / "scorecards" / "OCR_parsed_scorecards" / "SCORECARDS.csv",
}


def main() -> None:
    tables = {}
    for table_name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
        tables[table_name] = standardize_dataframe(read_csv_auto(path))

    save_tables(tables, BRONZE_DIR, REPORT_PATH)
    print_summary("UFC-DataLab", RAW_DIR, BRONZE_DIR, tables)


if __name__ == "__main__":
    main()
