"""Build and evaluate one pre-fight dataset using explicit historical features.

The historical input must contain snapshots known before the fighter's bouts
on each event date. A future bout therefore requires a new snapshot for that
date; copying the last ``*_antes`` row would omit the fighter's latest bout.
No function here rebuilds the upstream history or fits the temporal clusters.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


TARGET = "alvo_red_vence"
HISTORICAL_METRICS = [
    "sig_str_min_antes",
    "sig_str_recebidos_min_antes",
    "td_15min_antes",
    "td_tent_15min_antes",
    "sub_15min_antes",
    "rev_15min_antes",
    "kd_15min_antes",
    "ctrl_pct_antes",
    "sig_str_acc_antes",
    "str_def_antes",
    "td_acc_antes",
    "td_def_antes",
]
HISTORICAL_CONTEXT = [
    "qtd_lutas_anteriores",
    "taxa_vitoria_anterior",
    "dias_ultima_luta",
    "fl_estreante",
]
CLUSTER_CATEGORIES = ["grupo_temporal", "cluster_anterior_tecnico"]
CLUSTER_INDICATORS = [
    "alterou_perfil_desde_ultima",
    "houve_transicao_ate_dia",
]
CLUSTER_COUNTS = ["qtd_transicoes_ate_dia"]
METADATA = ["id_luta_pre_luta", "event_date", "red_fighter_id", "blue_fighter_id"]


def _require_columns(frame: pd.DataFrame, columns: list[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Colunas ausentes em {name}: {missing}")


def _normalize_ids(series: pd.Series, name: str) -> pd.Series:
    normalized = series.astype("string").str.strip().replace("", pd.NA)
    if normalized.isna().any():
        raise ValueError(f"Há identificadores ausentes em {name}.")
    return normalized


def _normalize_dates(series: pd.Series, name: str) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"Há datas ausentes ou inválidas em {name}.")
    if isinstance(parsed.dtype, pd.DatetimeTZDtype):
        parsed = parsed.dt.tz_localize(None)
    return parsed.dt.normalize()


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype(float).replace(
        [np.inf, -np.inf], np.nan
    )


def _indicator(series: pd.Series, name: str) -> pd.Series:
    """Convert bool, 0/1 and their string forms without bool('False')."""
    mapping = {
        "true": 1.0, "false": 0.0,
        "1": 1.0, "0": 0.0, "1.0": 1.0, "0.0": 0.0,
    }
    converted = series.astype("string").str.strip().str.lower().map(mapping)
    invalid = series.notna() & converted.isna()
    if invalid.any():
        values = series.loc[invalid].astype(str).unique().tolist()
        raise ValueError(f"Indicador {name} deve conter 0/1 ou True/False: {values}")
    return converted.astype(float)


def _category(series: pd.Series) -> pd.Series:
    values = series.astype("string").str.strip().replace("", pd.NA)
    return values.astype(object).where(values.notna(), np.nan)


def _validate_target(frame: pd.DataFrame, name: str) -> pd.Series:
    _require_columns(frame, [TARGET], name)
    target = pd.to_numeric(frame[TARGET], errors="coerce")
    if target.isna().any() or not target.isin([0, 1]).all():
        raise ValueError(f"{name} deve conter somente alvos conhecidos 0/1.")
    if target.nunique() != 2:
        raise ValueError(f"{name} precisa conter as duas classes do alvo.")
    return target.astype("int8")


def construir_base_pre_luta(
    lutas: pd.DataFrame,
    hist: pd.DataFrame,
    cadastro: pd.DataFrame,
    apos_calibracao=None,
    *,
    exigir_resultado: bool = True,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Create one historical + physical + temporal-cluster feature table.

    Only complementary W/L results are retained by default. With
    ``exigir_resultado=False``, missing results are allowed and TARGET is NaN
    for an unknown outcome. That mode still requires a valid historical
    snapshot on the exact bout date and the pre-computed cluster columns.
    It never substitutes an outdated last available snapshot.

    Missing-value flags in history are optional for already-missing inputs.
    When present, they are validated and restore NaN before imputation. The
    flags are preserved for auditing; the numeric imputer creates its own
    missingness indicators, so the flags are not duplicated in the spec.
    """
    cluster_categories = [
        f"{corner}_{column}"
        for corner in ["red", "blue"]
        for column in CLUSTER_CATEGORIES
    ]
    cluster_numeric = [
        f"{corner}_{column}"
        for corner in ["red", "blue"]
        for column in CLUSTER_INDICATORS + CLUSTER_COUNTS
    ]
    required_fights = [
        "event_date", "red_fighter_id", "blue_fighter_id", "bout_type",
        *cluster_categories, *cluster_numeric,
    ]
    _require_columns(lutas, required_fights, "lutas com clusters/transições")
    if exigir_resultado:
        _require_columns(
            lutas, ["red_fighter_result", "blue_fighter_result"], "lutas"
        )

    source = lutas.copy(deep=True)
    source["event_date"] = _normalize_dates(source["event_date"], "lutas")
    for corner in ["red", "blue"]:
        column = f"{corner}_fighter_id"
        source[column] = _normalize_ids(source[column], column)
    if source["red_fighter_id"].eq(source["blue_fighter_id"]).any():
        raise ValueError("Uma luta não pode ter o mesmo lutador nos dois cantos.")
    if "id_luta_pre_luta" not in source.columns:
        source["id_luta_pre_luta"] = np.arange(len(source))
    if source["id_luta_pre_luta"].isna().any() or source[
        "id_luta_pre_luta"
    ].duplicated().any():
        raise ValueError("id_luta_pre_luta deve ser único e não ausente.")

    red_result = source.get(
        "red_fighter_result", pd.Series(pd.NA, index=source.index)
    ).astype("string").str.strip().str.upper()
    blue_result = source.get(
        "blue_fighter_result", pd.Series(pd.NA, index=source.index)
    ).astype("string").str.strip().str.upper()
    decisive = (
        (red_result.eq("W") & blue_result.eq("L"))
        | (red_result.eq("L") & blue_result.eq("W"))
    ).fillna(False)

    # Explicit allowlist: current-bout statistics and outcomes are not copied.
    base = source[[*METADATA, "bout_type", *cluster_categories, *cluster_numeric]].copy()
    base[TARGET] = np.nan
    base.loc[decisive, TARGET] = red_result.loc[decisive].eq("W").astype("int8")
    if exigir_resultado:
        base = base.loc[decisive].copy()
        base[TARGET] = base[TARGET].astype("int8")
    if apos_calibracao is not None:
        cutoff = pd.to_datetime(apos_calibracao, errors="coerce")
        if pd.isna(cutoff):
            raise ValueError("apos_calibracao deve ser uma data válida.")
        cutoff = pd.Timestamp(cutoff)
        if cutoff.tzinfo is not None:
            cutoff = cutoff.tz_localize(None)
        base = base.loc[base["event_date"].gt(cutoff.normalize())].copy()
    if base.empty:
        raise ValueError("Nenhuma luta elegível após os filtros pré-luta.")

    historical_columns = HISTORICAL_CONTEXT + HISTORICAL_METRICS
    if "sig_str_tent_min_antes" in hist.columns:
        historical_columns = historical_columns + ["sig_str_tent_min_antes"]
    _require_columns(
        hist, ["fighter_id", "event_date", *historical_columns], "histórico pré-luta"
    )
    flags = [
        f"{column}_sem_dado_antes"
        for column in historical_columns
        if f"{column}_sem_dado_antes" in hist.columns
    ]
    history = hist[["fighter_id", "event_date", *historical_columns, *flags]].copy()
    history["fighter_id"] = _normalize_ids(history["fighter_id"], "hist.fighter_id")
    history["event_date"] = _normalize_dates(history["event_date"], "histórico")
    for column in historical_columns:
        history[column] = (
            _indicator(history[column], column)
            if column == "fl_estreante"
            else _numeric(history[column])
        )
        flag = f"{column}_sem_dado_antes"
        if flag in flags:
            history[flag] = _indicator(history[flag], flag)
            history.loc[history[flag].eq(1), column] = np.nan

    conflicts = (
        history.groupby(["fighter_id", "event_date"])[historical_columns + flags]
        .nunique(dropna=False).gt(1).any(axis=1)
    )
    if conflicts.any():
        examples = conflicts[conflicts].index.tolist()[:5]
        raise ValueError(
            "Históricos conflitantes para o mesmo lutador e data: "
            f"{examples}. Não é possível escolher uma luta arbitrariamente."
        )
    history = history.drop_duplicates(["fighter_id", "event_date"])

    _require_columns(
        cadastro, ["fighter_id", "date_of_birth", "height_cm", "reach_cm"], "cadastro"
    )
    physical = cadastro[["fighter_id", "date_of_birth", "height_cm", "reach_cm"]].copy()
    physical["fighter_id"] = _normalize_ids(physical["fighter_id"], "cadastro.fighter_id")
    if physical["fighter_id"].duplicated().any():
        raise ValueError("cadastro deve ter uma única linha por fighter_id.")
    physical["date_of_birth"] = pd.to_datetime(physical["date_of_birth"], errors="coerce")
    if isinstance(physical["date_of_birth"].dtype, pd.DatetimeTZDtype):
        physical["date_of_birth"] = physical["date_of_birth"].dt.tz_localize(None)
    for column in ["height_cm", "reach_cm"]:
        physical[column] = _numeric(physical[column]).where(
            _numeric(physical[column]).gt(0)
        )

    numeric_features: list[str] = []
    for corner in ["red", "blue"]:
        fighter_id = f"{corner}_fighter_id"
        rename_history = {
            "fighter_id": fighter_id,
            **{column: f"{corner}_{column}" for column in historical_columns + flags},
        }
        base = base.merge(
            history.rename(columns=rename_history),
            on=[fighter_id, "event_date"], how="left", validate="many_to_one",
            indicator="_historico_encontrado", sort=False,
        )
        absent = base["_historico_encontrado"].ne("both")
        if absent.any():
            examples = base.loc[absent, [fighter_id, "event_date"]].head().to_dict("records")
            raise ValueError(
                f"Falta snapshot pré-luta para {corner} na data exata: {examples}. "
                "Atualize o histórico até a véspera; não copie o último *_antes."
            )
        base = base.drop(columns="_historico_encontrado")
        numeric_features.extend(f"{corner}_{column}" for column in historical_columns)

        renamed_physical = physical.rename(columns={
            "fighter_id": fighter_id,
            "date_of_birth": f"_{corner}_date_of_birth",
            "height_cm": f"{corner}_height_cm",
            "reach_cm": f"{corner}_reach_cm",
        })
        base = base.merge(renamed_physical, on=fighter_id, how="left", validate="many_to_one")
        birthday = base[f"_{corner}_date_of_birth"]
        age = (base["event_date"] - birthday).dt.total_seconds() / (365.2425 * 86400)
        base[f"{corner}_age_at_fight"] = age.where(age.ge(0))
        base = base.drop(columns=f"_{corner}_date_of_birth")
        numeric_features.extend([
            f"{corner}_age_at_fight", f"{corner}_height_cm", f"{corner}_reach_cm",
        ])
        for column in CLUSTER_INDICATORS:
            name = f"{corner}_{column}"
            base[name] = _indicator(base[name], name)
        count_column = f"{corner}_qtd_transicoes_ate_dia"
        base[count_column] = _numeric(base[count_column])
        invalid_counts = base[count_column].notna() & (
            base[count_column].lt(0) | base[count_column].mod(1).ne(0)
        )
        if invalid_counts.any():
            raise ValueError(f"{count_column} deve conter contagens inteiras não negativas.")

    categorical_features = ["bout_type", *cluster_categories]
    for column in categorical_features:
        base[column] = _category(base[column])
    spec = {
        "numericas": numeric_features + cluster_numeric,
        "categoricas": categorical_features,
    }
    return base.sort_values(["event_date", "id_luta_pre_luta"], kind="stable").reset_index(drop=True), spec


def dividir_temporal(
    base: pd.DataFrame, fracao_teste: float = 0.2
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    """Reserve the latest event dates; never split a date across the sets."""
    if not 0 < fracao_teste < 1:
        raise ValueError("fracao_teste deve estar entre 0 e 1.")
    _require_columns(base, ["event_date", TARGET], "base pré-luta")
    _validate_target(base, "base pré-luta")
    dated = base.copy()
    dated["event_date"] = _normalize_dates(dated["event_date"], "base pré-luta")
    dates = dated["event_date"].drop_duplicates().sort_values().reset_index(drop=True)
    if len(dates) < 2:
        raise ValueError("São necessárias pelo menos duas datas distintas.")
    n_test_dates = min(max(1, math.ceil(len(dates) * fracao_teste)), len(dates) - 1)
    cutoff = pd.Timestamp(dates.iloc[-n_test_dates])
    train = dated.loc[dated["event_date"].lt(cutoff)].copy()
    test = dated.loc[dated["event_date"].ge(cutoff)].copy()
    _validate_target(train, "treino pré-luta")
    _validate_target(test, "teste pré-luta")
    return train.sort_values("event_date", kind="stable"), test.sort_values("event_date", kind="stable"), cutoff


def criar_preprocessamento_pre_luta(
    numericas: list[str], categoricas: list[str]
) -> ColumnTransformer:
    """Define preprocessing; all learned values are fitted by the model pipeline."""
    return ColumnTransformer([
        (
            "numericas",
            Pipeline([
                ("imputacao", SimpleImputer(
                    strategy="median", add_indicator=True, keep_empty_features=True,
                )),
                ("escala", StandardScaler()),
            ]),
            list(numericas),
        ),
        (
            "categoricas",
            Pipeline([
                ("imputacao", SimpleImputer(
                    strategy="constant", fill_value="Sem informação", keep_empty_features=True,
                )),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]),
            list(categoricas),
        ),
    ], remainder="drop")


def _features_from_spec(spec: dict[str, list[str]]) -> list[str]:
    if "numericas" not in spec or "categoricas" not in spec:
        raise ValueError("spec deve conter as listas numericas e categoricas.")
    features = list(spec["numericas"]) + list(spec["categoricas"])
    if not features or len(features) != len(set(features)):
        raise ValueError("As features devem ser não vazias e sem nomes repetidos.")
    forbidden = set(METADATA + [TARGET, "round", "bonus", "method", "red_fighter_result", "blue_fighter_result"])
    if forbidden.intersection(features):
        raise ValueError("Metadados, resultados e desfechos não podem entrar como features.")
    return features


def treinar_modelos_pre_luta(
    treino: pd.DataFrame, teste: pd.DataFrame, spec: dict[str, list[str]]
) -> tuple[pd.DataFrame, dict[str, Pipeline], dict[str, dict[str, np.ndarray]]]:
    """Fit the three initial classifiers on one integrated pre-fight dataset."""
    features = _features_from_spec(spec)
    _require_columns(treino, features + ["event_date", TARGET], "treino pré-luta")
    _require_columns(teste, features + ["event_date", TARGET], "teste pré-luta")
    train_dates = _normalize_dates(treino["event_date"], "treino pré-luta")
    test_dates = _normalize_dates(teste["event_date"], "teste pré-luta")
    if train_dates.max() >= test_dates.min():
        raise ValueError("O treino deve terminar antes de todas as datas do teste.")
    y_train = _validate_target(treino, "treino pré-luta")
    y_test = _validate_target(teste, "teste pré-luta")
    preprocessing = criar_preprocessamento_pre_luta(spec["numericas"], spec["categoricas"])
    classifiers = {
        "Referência majoritária": DummyClassifier(strategy="prior"),
        "Logística": LogisticRegression(max_iter=3000, C=1.0, random_state=42),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=3, random_state=42, n_jobs=-1,
        ),
    }
    models: dict[str, Pipeline] = {}
    predictions: dict[str, dict[str, np.ndarray]] = {}
    rows = []
    for name, classifier in classifiers.items():
        model = Pipeline([
            ("preprocessamento", clone(preprocessing)),
            ("classificador", clone(classifier)),
        ])
        model.fit(treino[features], y_train)
        predicted = model.predict(teste[features])
        probabilities = model.predict_proba(teste[features])[:, list(model.classes_).index(1)]
        rows.append({
            "modelo": name,
            "acuracia": accuracy_score(y_test, predicted),
            "acuracia_balanceada": balanced_accuracy_score(y_test, predicted),
            "f1_macro": f1_score(y_test, predicted, average="macro", zero_division=0),
            "roc_auc": roc_auc_score(y_test, probabilities),
            "log_loss": log_loss(y_test, probabilities, labels=[0, 1]),
            "brier": brier_score_loss(y_test, probabilities),
        })
        models[name] = model
        predictions[name] = {"classe": predicted, "probabilidade_red": probabilities}
    return pd.DataFrame(rows), models, predictions


def prever_confrontos_pre_luta(
    modelo: Pipeline, base_confrontos: pd.DataFrame, spec: dict[str, list[str]]
) -> pd.DataFrame:
    """Score an already-prepared card, without fitting or creating snapshots."""
    features = _features_from_spec(spec)
    _require_columns(base_confrontos, METADATA + features, "confrontos pré-luta")
    probabilities = modelo.predict_proba(base_confrontos[features])[
        :, list(modelo.classes_).index(1)
    ]
    result = base_confrontos[METADATA].copy()
    result["probabilidade_red"] = probabilities
    result["probabilidade_blue"] = 1 - probabilities
    predicted = modelo.predict(base_confrontos[features])
    result["vencedor_previsto"] = np.where(predicted == 1, "Red", "Blue")
    return result
