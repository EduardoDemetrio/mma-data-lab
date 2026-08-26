from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd


MISSING_MARKERS = {"", "-", "--", "---", "nan", "NaN", "N/A", "n/a", "NULL", "null"}


def normalize_column_name(column: str) -> str:
    without_accents = unicodedata.normalize("NFKD", str(column))
    without_accents = without_accents.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", without_accents.strip().lower())
    normalized = normalized.strip("_")

    replacements = {
        "atmpted": "attempted",
        "sig_str": "significant_strikes",
        "td": "takedowns",
        "dob": "date_of_birth",
        "ctrl": "control_time",
        "r_": "red_",
        "b_": "blue_",
    }
    for old, new in replacements.items():
        if normalized == old.rstrip("_"):
            normalized = new.rstrip("_")
        elif normalized.startswith(old):
            normalized = new + normalized[len(old) :]

    return normalized


def normalize_text(value: object) -> object:
    if not isinstance(value, str):
        return value

    cleaned = value.strip()
    if cleaned in MISSING_MARKERS:
        return pd.NA
    return cleaned


def clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column in df.select_dtypes(include=["object"]).columns:
        df[column] = df[column].map(normalize_text)
    return df


def standardize_columns(df: pd.DataFrame, rename_map: dict[str, str] | None = None) -> pd.DataFrame:
    rename_map = rename_map or {}
    return df.rename(
        columns={
            column: rename_map.get(column, normalize_column_name(column))
            for column in df.columns
        }
    )


def detect_delimiter(path: Path) -> str:
    first_line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    comma = first_line.count(",")
    semicolon = first_line.count(";")
    tab = first_line.count("\t")

    if semicolon > comma and semicolon > tab:
        return ";"
    if tab > comma:
        return "\t"
    return ","


def read_csv_auto(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=detect_delimiter(path), low_memory=False)


def read_json_lines(path: Path) -> pd.DataFrame:
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return pd.json_normalize(rows)


def serialize_complex_values(df: pd.DataFrame) -> pd.DataFrame:
    """Convert list/dict cells to JSON strings so CSV export and duplicate checks work."""

    df = df.copy()
    for column in df.columns:
        if df[column].dtype != "object":
            continue

        has_complex_values = df[column].map(lambda value: isinstance(value, (list, dict))).any()
        if not has_complex_values:
            continue

        df[column] = df[column].map(
            lambda value: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
        )

    return df


def parse_dates_by_name(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column in df.columns:
        if re.search(r"(^date$|_date$|date_of_birth|event_date|birth)", column):
            sample = df[column].dropna().astype(str).head(25)
            uses_year_first = sample.str.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$").any()
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
                dayfirst=not uses_year_first,
            )
    return df


def parse_percent(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    text = str(value).replace("%", "").strip()
    if text in MISSING_MARKERS:
        return pd.NA
    try:
        return float(text)
    except ValueError:
        return pd.NA


def parse_ratio(value: object) -> tuple[object, object]:
    if pd.isna(value):
        return pd.NA, pd.NA
    match = re.match(r"^\s*(\d+)\s+of\s+(\d+)\s*$", str(value))
    if not match:
        return pd.NA, pd.NA
    return int(match.group(1)), int(match.group(2))


def parse_time_to_seconds(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    match = re.match(r"^(\d+):(\d{2})$", str(value).strip())
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
    return round((int(match.group(1)) * 12 + int(match.group(2))) * 2.54, 2)


def parse_first_number(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    match = re.search(r"\d+(\.\d+)?", str(value))
    if not match:
        return pd.NA
    return float(match.group())


def add_generic_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for column in list(df.columns):
        if df[column].dtype != "object":
            continue

        sample = df[column].dropna().astype(str).head(20)
        if sample.empty:
            continue

        if sample.str.match(r"^\d+\s+of\s+\d+$").any():
            parsed = df[column].map(parse_ratio)
            df[f"{column}_landed"] = parsed.map(lambda item: item[0])
            df[f"{column}_attempted"] = parsed.map(lambda item: item[1])
        elif column.endswith("_pct") or column.endswith("_acc") or "percent" in column:
            df[f"{column}_num"] = df[column].map(parse_percent)
        elif "time" in column and sample.str.match(r"^\d+:\d{2}$").any():
            df[f"{column}_seconds"] = df[column].map(parse_time_to_seconds)

    for column in list(df.columns):
        if column.endswith("height") or column.endswith("height_cms"):
            continue
        if column in {"height", "red_height", "blue_height"}:
            df[f"{column}_cm"] = df[column].map(parse_height_to_cm)
        if column in {"weight", "red_weight", "blue_weight"}:
            df[f"{column}_lbs"] = df[column].map(parse_first_number)
        if column in {"reach", "red_reach", "blue_reach"}:
            df[f"{column}_inches"] = df[column].map(parse_first_number)

    return df


def standardize_dataframe(df: pd.DataFrame, rename_map: dict[str, str] | None = None) -> pd.DataFrame:
    df = serialize_complex_values(df)
    df = standardize_columns(df, rename_map=rename_map)
    df = clean_strings(df)
    df = parse_dates_by_name(df)
    df = add_generic_derived_columns(df)
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


def save_tables(
    tables: dict[str, pd.DataFrame],
    output_dir: Path,
    report_path: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    for table_name, df in tables.items():
        df.to_csv(output_dir / f"{table_name}.csv", index=False, encoding="utf-8")

    build_quality_report(tables).to_csv(report_path, index=False, encoding="utf-8")


def print_summary(source_name: str, input_dir: Path, output_dir: Path, tables: dict[str, pd.DataFrame]) -> None:
    report = build_quality_report(tables)
    print(f"Padronizacao concluida para {source_name}.")
    print(f"Entrada: {input_dir}")
    print(f"Saida: {output_dir}")
    print(report[["table_name", "rows", "columns", "duplicated_rows", "total_missing_values"]])
