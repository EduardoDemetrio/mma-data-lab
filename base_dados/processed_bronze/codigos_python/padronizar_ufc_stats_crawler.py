from __future__ import annotations

from pathlib import Path

from padronizacao_utils import (
    print_summary,
    read_csv_auto,
    read_json_lines,
    save_tables,
    standardize_dataframe,
)


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "raw" / "repos_investigacao" / "ufc-stats-crawler"
BRONZE_DIR = BASE_DIR / "processed_bronze" / "ufc_stats_crawler"
REPORT_PATH = BASE_DIR / "docs" / "qualidade_bronze_ufc_stats_crawler.csv"


FILES = {
    "fight_info": RAW_DIR / "data" / "fight_info" / "2019-12-11T15-15-57.csv",
    "fight_stats": RAW_DIR / "data" / "fight_stats" / "2019-12-11T15-15-57.jl",
    "fighter_stats": RAW_DIR / "data" / "fighter_stats" / "2019-12-11T23-32-40.csv",
    "upcoming": RAW_DIR / "data" / "upcoming" / "2020-02-06T16-49-53.csv",
}


def load_table(path: Path):
    if path.suffix.lower() == ".jl":
        return read_json_lines(path)
    return read_csv_auto(path)


def main() -> None:
    tables = {}
    for table_name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
        tables[table_name] = standardize_dataframe(load_table(path))

    save_tables(tables, BRONZE_DIR, REPORT_PATH)
    print_summary("ufc-stats-crawler", RAW_DIR, BRONZE_DIR, tables)


if __name__ == "__main__":
    main()
