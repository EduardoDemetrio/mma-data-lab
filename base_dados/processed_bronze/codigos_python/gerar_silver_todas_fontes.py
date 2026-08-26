from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd

from padronizacao_utils import build_quality_report


BASE_DADOS_DIR = Path(__file__).resolve().parents[2]
BRONZE_DIR = BASE_DADOS_DIR / "processed_bronze"
SILVER_DIR = BASE_DADOS_DIR / "processed_silver"
DOCS_DIR = BASE_DADOS_DIR / "docs"
CODE_DIR_NAME = "codigos_python"


def normalize_fighter_name(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    text = str(value).strip().upper()
    text = re.sub(r"\s+", " ", text)
    return text if text else pd.NA


def parse_american_odds(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    try:
        odds = float(value)
    except (TypeError, ValueError):
        return pd.NA

    if odds > 0:
        return round(100 / (odds + 100), 6)
    if odds < 0:
        return round(abs(odds) / (abs(odds) + 100), 6)
    return pd.NA


def parse_boolean(value: object) -> object:
    if pd.isna(value):
        return pd.NA

    text = str(value).strip().lower()
    if text in {"1", "true", "t", "yes", "y", "sim"}:
        return True
    if text in {"0", "false", "f", "no", "n", "nao", "não"}:
        return False
    return pd.NA


def parse_round_time_to_seconds(value: object) -> object:
    if pd.isna(value):
        return pd.NA

    match = re.match(r"^(\d+):(\d{2})$", str(value).strip())
    if not match:
        return pd.NA

    return int(match.group(1)) * 60 + int(match.group(2))


def add_metadata_columns(df: pd.DataFrame, source_name: str, table_name: str) -> pd.DataFrame:
    df = df.copy()
    if "silver_source" not in df.columns:
        df.insert(0, "silver_source", source_name)
    if "silver_table" not in df.columns:
        df.insert(1, "silver_table", table_name)
    if "silver_row_id" not in df.columns:
        df.insert(2, "silver_row_id", range(1, len(df) + 1))
    return df


def add_date_parts(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column in list(df.columns):
        if not re.search(r"(^date$|_date$|date_of_birth|event_date)", column):
            continue

        parsed = pd.to_datetime(df[column], errors="coerce")
        if parsed.notna().sum() == 0:
            continue

        df[f"{column}_year"] = parsed.dt.year
        df[f"{column}_month"] = parsed.dt.month
        df[f"{column}_day"] = parsed.dt.day

    return df


def add_name_normalizations(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column in list(df.columns):
        if column.endswith("fighter") or column.endswith("fighter_name") or column in {
            "fighter_name",
            "winner_name",
            "loser_name",
            "red_fighter_name",
            "blue_fighter_name",
            "red_fighter",
            "blue_fighter",
        }:
            df[f"{column}_norm"] = df[column].map(normalize_fighter_name)
    return df


def add_odds_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column in list(df.columns):
        if column.endswith("_odds") or column in {"red_odds", "blue_odds"}:
            df[f"{column}_implied_prob"] = df[column].map(parse_american_odds)
    return df


def add_boolean_helpers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column in list(df.columns):
        if column in {"title_bout", "title_fight", "empty_arena"}:
            df[f"{column}_bool"] = df[column].map(parse_boolean)
    return df


def add_time_helpers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for column in list(df.columns):
        if column.endswith("_time") or column in {"time", "finish_round_time"}:
            sample = df[column].dropna().astype(str).head(20)
            if not sample.str.match(r"^\d+:\d{2}$").any():
                continue
            df[f"{column}_seconds_in_round"] = df[column].map(parse_round_time_to_seconds)

    if "finish_round" in df.columns and "finish_round_time_seconds_in_round" in df.columns:
        finish_round = pd.to_numeric(df["finish_round"], errors="coerce")
        seconds = pd.to_numeric(df["finish_round_time_seconds_in_round"], errors="coerce")
        df["estimated_total_fight_time_seconds"] = ((finish_round - 1) * 300 + seconds).where(
            finish_round.notna() & seconds.notna()
        )

    return df


def add_age_helpers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    event_date_col = None
    for candidate in ["event_date", "date"]:
        if candidate in df.columns:
            event_date_col = candidate
            break

    if event_date_col is None:
        return df

    event_date = pd.to_datetime(df[event_date_col], errors="coerce")
    for birth_col in [column for column in df.columns if column.endswith("date_of_birth")]:
        birth_date = pd.to_datetime(df[birth_col], errors="coerce")
        age_col = birth_col.removesuffix("date_of_birth").rstrip("_")
        if age_col:
            output_col = f"{age_col}_age_at_event"
        else:
            output_col = "age_at_event"
        df[output_col] = ((event_date - birth_date).dt.days / 365.25).round(2)

    return df


def add_fight_key(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    candidates = [
        column
        for column in [
            "event_name",
            "event_date",
            "date",
            "bout",
            "red_fighter_name",
            "blue_fighter_name",
            "red_fighter",
            "blue_fighter",
            "fighter_1",
            "fighter_2",
            "fight_id",
        ]
        if column in df.columns
    ]

    if len(candidates) < 2:
        return df

    def make_key(row: pd.Series) -> str:
        raw_key = "|".join("" if pd.isna(row[column]) else str(row[column]) for column in candidates)
        return hashlib.sha1(raw_key.encode("utf-8")).hexdigest()

    df["silver_fight_key"] = df[candidates].apply(make_key, axis=1)
    return df


def build_silver_table(df: pd.DataFrame, source_name: str, table_name: str) -> pd.DataFrame:
    df = add_metadata_columns(df, source_name, table_name)
    df = add_date_parts(df)
    df = add_name_normalizations(df)
    df = add_odds_metrics(df)
    df = add_boolean_helpers(df)
    df = add_time_helpers(df)
    df = add_age_helpers(df)
    df = add_fight_key(df)
    return df


def iter_bronze_csvs() -> list[Path]:
    return sorted(
        path
        for path in BRONZE_DIR.rglob("*.csv")
        if CODE_DIR_NAME not in path.parts and path.is_file()
    )


def main() -> None:
    all_reports = {}
    for input_path in iter_bronze_csvs():
        relative_path = input_path.relative_to(BRONZE_DIR)
        source_name = relative_path.parts[0]
        table_name = input_path.stem
        output_path = SILVER_DIR / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        bronze_df = pd.read_csv(input_path, low_memory=False)
        silver_df = build_silver_table(bronze_df, source_name, table_name)
        silver_df.to_csv(output_path, index=False, encoding="utf-8")
        all_reports[f"{source_name}/{table_name}"] = silver_df

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    report = build_quality_report(all_reports)
    report.to_csv(DOCS_DIR / "qualidade_silver_todas_fontes.csv", index=False, encoding="utf-8")

    print("Geracao da camada silver concluida.")
    print(f"Entrada: {BRONZE_DIR}")
    print(f"Saida: {SILVER_DIR}")
    print(report[["table_name", "rows", "columns", "duplicated_rows", "total_missing_values"]])


if __name__ == "__main__":
    main()
