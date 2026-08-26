from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "raw" / "repos_investigacao" / "scrape_ufc_stats"
BRONZE_DIR = BASE_DIR / "processed_bronze" / "scrape_ufc_stats"
DOCS_DIR = BASE_DIR / "docs"


FILES = {
    "event_details": "ufc_event_details.csv",
    "fight_details": "ufc_fight_details.csv",
    "fight_results": "ufc_fight_results.csv",
    "fight_stats": "ufc_fight_stats.csv",
    "fighter_details": "ufc_fighter_details.csv",
    "fighter_tott": "ufc_fighter_tott.csv",
}


RENAME_COLUMNS = {
    "EVENT": "event_name",
    "BOUT": "bout",
    "URL": "url",
    "DATE": "event_date",
    "LOCATION": "event_location",
    "OUTCOME": "outcome",
    "WEIGHTCLASS": "weight_class",
    "METHOD": "method",
    "ROUND": "round",
    "TIME": "time",
    "TIME FORMAT": "time_format",
    "REFEREE": "referee",
    "DETAILS": "details",
    "FIGHTER": "fighter_name",
    "KD": "knockdowns",
    "SIG.STR.": "sig_str",
    "SIG.STR. %": "sig_str_pct",
    "TOTAL STR.": "total_str",
    "TD": "takedowns",
    "TD %": "takedown_pct",
    "SUB.ATT": "submission_attempts",
    "REV.": "reversals",
    "CTRL": "control_time",
    "HEAD": "head_str",
    "BODY": "body_str",
    "LEG": "leg_str",
    "DISTANCE": "distance_str",
    "CLINCH": "clinch_str",
    "GROUND": "ground_str",
    "FIRST": "first_name",
    "LAST": "last_name",
    "NICKNAME": "nickname",
    "HEIGHT": "height",
    "WEIGHT": "weight",
    "REACH": "reach",
    "STANCE": "stance",
    "DOB": "date_of_birth",
}


RATIO_COLUMNS = [
    "sig_str",
    "total_str",
    "takedowns",
    "head_str",
    "body_str",
    "leg_str",
    "distance_str",
    "clinch_str",
    "ground_str",
]


PERCENT_COLUMNS = ["sig_str_pct", "takedown_pct"]


def normalize_text(value: object) -> object:
    """Trim strings and convert source placeholders to missing values."""

    if not isinstance(value, str):
        return value

    cleaned = value.strip()
    if cleaned in {"", "-", "--", "---"}:
        return pd.NA
    return cleaned


def normalize_column_name(column: str) -> str:
    """Fallback normalizer for columns not listed in RENAME_COLUMNS."""

    without_accents = unicodedata.normalize("NFKD", column)
    without_accents = without_accents.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", without_accents.strip().lower())
    return normalized.strip("_")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {
        column: RENAME_COLUMNS.get(column, normalize_column_name(column))
        for column in df.columns
    }
    return df.rename(columns=renamed)


def clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    object_columns = df.select_dtypes(include=["object"]).columns
    for column in object_columns:
        df[column] = df[column].map(normalize_text)
    return df


def parse_date_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in df.columns:
        return df

    df = df.copy()
    df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def parse_round(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    match = re.search(r"\d+", str(value))
    if not match:
        return pd.NA
    return int(match.group())


def parse_percent(value: object) -> object:
    if pd.isna(value):
        return pd.NA

    text = str(value).replace("%", "").strip()
    if text in {"", "-", "--", "---"}:
        return pd.NA

    try:
        return float(text)
    except ValueError:
        return pd.NA


def parse_ratio(value: object) -> tuple[object, object]:
    """Parse UFCStats values like '12 of 31' into landed/attempted."""

    if pd.isna(value):
        return pd.NA, pd.NA

    match = re.match(r"^\s*(\d+)\s+of\s+(\d+)\s*$", str(value))
    if not match:
        return pd.NA, pd.NA

    return int(match.group(1)), int(match.group(2))


def parse_time_to_seconds(value: object) -> object:
    if pd.isna(value):
        return pd.NA

    text = str(value).strip()
    match = re.match(r"^(\d+):(\d{2})$", text)
    if not match:
        return pd.NA

    return int(match.group(1)) * 60 + int(match.group(2))


def parse_height_to_cm(value: object) -> object:
    if pd.isna(value):
        return pd.NA

    text = str(value).replace('"', "").strip()
    match = re.match(r"^(\d+)'\s*(\d+)$", text)
    if not match:
        return pd.NA

    feet = int(match.group(1))
    inches = int(match.group(2))
    return round((feet * 12 + inches) * 2.54, 2)


def parse_measure_to_number(value: object) -> object:
    if pd.isna(value):
        return pd.NA

    match = re.search(r"\d+(\.\d+)?", str(value))
    if not match:
        return pd.NA
    return float(match.group())


def add_ratio_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column in RATIO_COLUMNS:
        if column not in df.columns:
            continue

        parsed = df[column].map(parse_ratio)
        df[f"{column}_landed"] = parsed.map(lambda item: item[0])
        df[f"{column}_attempted"] = parsed.map(lambda item: item[1])

    return df


def standardize_event_details(df: pd.DataFrame) -> pd.DataFrame:
    df = parse_date_column(df, "event_date")
    return df


def standardize_fight_results(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "round" in df.columns:
        df["round_number"] = df["round"].map(parse_round)
    return df


def standardize_fight_stats(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "round" in df.columns:
        df["round_number"] = df["round"].map(parse_round)

    for column in ["knockdowns", "submission_attempts", "reversals"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in PERCENT_COLUMNS:
        if column in df.columns:
            df[f"{column}_num"] = df[column].map(parse_percent)

    if "control_time" in df.columns:
        df["control_seconds"] = df["control_time"].map(parse_time_to_seconds)

    return add_ratio_columns(df)


def standardize_fighter_tott(df: pd.DataFrame) -> pd.DataFrame:
    df = parse_date_column(df, "date_of_birth")
    df = df.copy()

    if "height" in df.columns:
        df["height_cm"] = df["height"].map(parse_height_to_cm)
    if "weight" in df.columns:
        df["weight_lbs"] = df["weight"].map(parse_measure_to_number)
    if "reach" in df.columns:
        df["reach_inches"] = df["reach"].map(parse_measure_to_number)
        df["reach_cm"] = df["reach_inches"].map(
            lambda value: round(value * 2.54, 2) if pd.notna(value) else pd.NA
        )

    return df


def load_raw_tables() -> dict[str, pd.DataFrame]:
    tables = {}
    for table_name, file_name in FILES.items():
        path = RAW_DIR / file_name
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")

        tables[table_name] = pd.read_csv(path)

    return tables


def standardize_table(table_name: str, df: pd.DataFrame) -> pd.DataFrame:
    df = standardize_columns(df)
    df = clean_strings(df)

    if table_name == "event_details":
        return standardize_event_details(df)
    if table_name == "fight_results":
        return standardize_fight_results(df)
    if table_name == "fight_stats":
        return standardize_fight_stats(df)
    if table_name == "fighter_tott":
        return standardize_fighter_tott(df)

    return df


def build_quality_report(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for table_name, df in tables.items():
        rows.append(
            {
                "table_name": table_name,
                "rows": len(df),
                "columns": len(df.columns),
                "duplicated_rows": int(df.duplicated().sum()),
                "total_missing_values": int(df.isna().sum().sum()),
                "columns_list": ", ".join(df.columns),
            }
        )
    return pd.DataFrame(rows)


def save_tables(tables: dict[str, pd.DataFrame]) -> None:
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    for table_name, df in tables.items():
        output_path = BRONZE_DIR / f"{table_name}.csv"
        df.to_csv(output_path, index=False, encoding="utf-8")

    report = build_quality_report(tables)
    report.to_csv(
        DOCS_DIR / "qualidade_bronze_scrape_ufc_stats.csv",
        index=False,
        encoding="utf-8",
    )


def main() -> None:
    raw_tables = load_raw_tables()
    standardized_tables = {
        table_name: standardize_table(table_name, df)
        for table_name, df in raw_tables.items()
    }
    save_tables(standardized_tables)

    report = build_quality_report(standardized_tables)
    print("Padronizacao concluida para scrape_ufc_stats.")
    print(f"Entrada: {RAW_DIR}")
    print(f"Saida: {BRONZE_DIR}")
    print(report[["table_name", "rows", "columns", "duplicated_rows", "total_missing_values"]])


if __name__ == "__main__":
    main()
