"""Prepare pre-fight fighter snapshots for the exploratory profiling stage."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "base_dados" / "processed_gold" / "df_historico.csv"
OUTPUT_PATH = (
    PROJECT_ROOT / "base_dados" / "processed_gold" / "perfis_lutadores_pre_luta.csv"
)
QUALITY_PATH = (
    PROJECT_ROOT / "base_dados" / "processed_gold"
    / "qualidade_perfis_lutadores_pre_luta.csv"
)

METADATA_COLUMNS = [
    "fight_id_hist",
    "event_date",
    "fighter_id",
    "corner",
    "result",
    "qtd_lutas_anteriores",
    "fl_estreante",
]

PROFILE_FEATURES = [
    "sig_str_min_antes",
    "sig_str_recebidos_min_antes",
    "sig_str_acc_antes",
    "str_def_antes",
    "td_15min_antes",
    "td_acc_antes",
    "td_def_antes",
    "sub_15min_antes",
    "ctrl_pct_antes",
    "pct_sig_str_distance_antes",
    "pct_sig_str_clinch_antes",
    "pct_sig_str_ground_antes",
]

PERCENTAGE_FEATURES = [
    "sig_str_acc_antes",
    "str_def_antes",
    "td_acc_antes",
    "td_def_antes",
    "ctrl_pct_antes",
    "pct_sig_str_distance_antes",
    "pct_sig_str_clinch_antes",
    "pct_sig_str_ground_antes",
]


def main() -> None:
    if not INPUT_PATH.is_file():
        raise FileNotFoundError(
            f"Arquivo de entrada não encontrado: {INPUT_PATH}. "
            "Execute o script a partir de uma cópia completa do projeto."
        )

    history = pd.read_csv(INPUT_PATH)
    required_columns = METADATA_COLUMNS + PROFILE_FEATURES
    missing_columns = sorted(set(required_columns) - set(history.columns))
    if missing_columns:
        raise ValueError(
            "A df_historico não contém as colunas esperadas: "
            + ", ".join(missing_columns)
        )

    issues: list[dict[str, object]] = []

    duplicate_pairs = history.duplicated(
        subset=["fighter_id", "fight_id_hist"], keep=False
    )
    if duplicate_pairs.any():
        issues.append(
            {
                "verificacao": "duplicidade_lutador_luta",
                "quantidade": int(duplicate_pairs.sum()),
                "detalhe": "Há mais de uma linha para o mesmo lutador e luta.",
            }
        )

    invalid_ids = history["fighter_id"].isna() | history["fight_id_hist"].isna()
    if invalid_ids.any():
        issues.append(
            {
                "verificacao": "identificadores_ausentes",
                "quantidade": int(invalid_ids.sum()),
                "detalhe": "Linhas sem fighter_id ou fight_id_hist.",
            }
        )

    parsed_dates = pd.to_datetime(history["event_date"], errors="coerce")
    invalid_dates = parsed_dates.isna()
    if invalid_dates.any():
        issues.append(
            {
                "verificacao": "datas_invalidas",
                "quantidade": int(invalid_dates.sum()),
                "detalhe": "event_date ausente ou não reconhecida como data.",
            }
        )

    dated_history = history.loc[~invalid_dates].copy()
    dated_history["_event_date_parsed"] = parsed_dates.loc[~invalid_dates]
    same_day = dated_history.duplicated(
        subset=["fighter_id", "_event_date_parsed"], keep=False
    )
    same_day_count = int(same_day.sum())
    if same_day_count:
        issues.append(
            {
                "verificacao": "lutas_mesmo_dia_por_lutador",
                "quantidade": same_day_count,
                "detalhe": (
                    "Registros do mesmo lutador e data precisam de desempate "
                    "temporal confiável para análises de evolução."
                ),
            }
        )

    profiles = history[required_columns].copy()
    profiles["event_date"] = parsed_dates
    numeric_conversion_issues = []
    for column in PROFILE_FEATURES:
        converted = pd.to_numeric(profiles[column], errors="coerce")
        conversion_failures = profiles[column].notna() & converted.isna()
        if conversion_failures.any():
            numeric_conversion_issues.append(
                {
                    "verificacao": f"conversao_numerica:{column}",
                    "quantidade": int(conversion_failures.sum()),
                    "detalhe": "Valores não numéricos encontrados; foram preservados como ausentes.",
                }
            )
        profiles[column] = converted
    issues.extend(numeric_conversion_issues)

    for column in PERCENTAGE_FEATURES:
        outside_range = profiles[column].notna() & ~profiles[column].between(0, 1)
        if outside_range.any():
            issues.append(
                {
                    "verificacao": f"percentual_fora_de_0_a_1:{column}",
                    "quantidade": int(outside_range.sum()),
                    "detalhe": "Percentuais esperados entre 0 e 1.",
                }
            )

    profiles = profiles.sort_values(
        ["fighter_id", "event_date", "fight_id_hist"],
        kind="stable",
        na_position="last",
    ).reset_index(drop=True)

    missingness = profiles[PROFILE_FEATURES].isna().sum()
    quality_rows = [
        {
            "verificacao": f"valores_ausentes:{column}",
            "quantidade": int(count),
            "detalhe": f"{count / len(profiles):.1%} das observações",
        }
        for column, count in missingness.items()
    ]
    quality_rows.extend(issues)
    if not issues:
        quality_rows.append(
            {
                "verificacao": "validacoes_estruturais",
                "quantidade": 0,
                "detalhe": "Nenhum problema estrutural encontrado nas verificações executadas.",
            }
        )
    quality = pd.DataFrame(
        quality_rows, columns=["verificacao", "quantidade", "detalhe"]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(OUTPUT_PATH, index=False)
    quality.to_csv(QUALITY_PATH, index=False)

    print(f"Observações de perfil: {len(profiles):,}")
    print(f"Lutadores: {profiles['fighter_id'].nunique():,}")
    print(f"Variáveis candidatas: {len(PROFILE_FEATURES)}")
    print(f"Base de perfis salva em: {OUTPUT_PATH}")
    print(f"Resumo de qualidade salvo em: {QUALITY_PATH}")
    print("\nValores ausentes nas variáveis candidatas:")
    print(missingness.to_string())
    if issues:
        print("\nPontos que precisam de revisão:")
        print(
            quality.loc[quality["verificacao"].isin(
                [issue["verificacao"] for issue in issues]
            )].to_string(index=False)
        )
    else:
        print("\nNenhum problema estrutural encontrado nas verificações executadas.")


if __name__ == "__main__":
    main()
