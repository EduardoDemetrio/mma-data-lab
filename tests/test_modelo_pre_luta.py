"""Checks for temporal feature construction, without fitting classifiers."""

import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from base_dados.modelo_pre_luta import (
    construir_base_pre_luta,
    dividir_temporal,
)


METRICAS_HISTORICAS = [
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


def criar_fixture():
    """Two distinct bouts per date make a date-preserving split observable."""
    datas = pd.date_range("2020-01-01", periods=6, freq="MS")
    atletas = ["a", "b", "c", "d"]
    lutas, historico = [], []

    for dia, data in enumerate(datas):
        for par, (vermelho, azul) in enumerate([("a", "b"), ("c", "d")]):
            vermelho_vence = (dia + par) % 2 == 0
            luta = {
                "event_date": data,
                "red_fighter_id": vermelho,
                "blue_fighter_id": azul,
                "red_fighter_result": "W" if vermelho_vence else "L",
                "blue_fighter_result": "L" if vermelho_vence else "W",
                "bout_type": "Lightweight Bout",
                "red_fighter_kd": dia + 1,
                "blue_fighter_kd": par,
                "red_fighter_sig_str_landed": 30 + dia,
                "blue_fighter_sig_str_landed": 20 + par,
                "round": 3,
                "time_seconds": 300,
                "method": "Decision - Unanimous",
                "bonus": 0,
                "red_fighter_pts_mean": 30,
                "blue_fighter_pts_mean": 27,
            }

            for cor in ["red", "blue"]:
                luta.update({
                    f"{cor}_grupo_temporal": "Perfil 0" if dia >= 2 else "Perfil inconclusivo",
                    f"{cor}_cluster_anterior_tecnico": "0" if dia >= 3 else None,
                    f"{cor}_alterou_perfil_desde_ultima": dia == 3,
                    f"{cor}_houve_transicao_ate_dia": dia >= 3,
                    f"{cor}_qtd_transicoes_ate_dia": int(dia >= 3),
                })

            lutas.append(luta)

            for cor, atleta in [("red", vermelho), ("blue", azul)]:
                linha = {
                    "fight_id_hist": dia * 2 + par,
                    "fighter_id": atleta,
                    "event_date": data,
                    "corner": cor,
                    "result": luta[f"{cor}_fighter_result"],
                    "qtd_lutas_anteriores": dia,
                    "qtd_vitorias_anteriores": dia // 2,
                    "qtd_derrotas_anteriores": dia - dia // 2,
                    "taxa_vitoria_anterior": 0.5,
                    "dias_ultima_luta": 30,
                    "fl_estreante": int(dia == 0),
                    "sig_str_tent_min_antes": 8.0 + dia / 10,
                }
                for indice, metrica in enumerate(METRICAS_HISTORICAS):
                    linha[metrica] = 0.1 * (indice + 1) + dia / 20
                for coluna in [
                    "qtd_lutas_anteriores", "qtd_vitorias_anteriores",
                    "qtd_derrotas_anteriores", "taxa_vitoria_anterior",
                    "dias_ultima_luta", "fl_estreante",
                    "sig_str_tent_min_antes", *METRICAS_HISTORICAS,
                ]:
                    linha[f"{coluna}_sem_dado_antes"] = 0
                historico.append(linha)

    cadastro = pd.DataFrame({
        "fighter_id": atletas,
        "date_of_birth": ["1988-06-15", "1990-02-20", "1991-09-10", "1987-12-25"],
        "height_cm": [175.0, 180.0, 178.0, 182.0],
        "reach_cm": [180.0, 184.0, 181.0, 186.0],
        # Lifetime snapshots must not leak into a historical prediction.
        "wins": [50, 60, 70, 80],
        "losses": [10, 11, 12, 13],
        "slpm": [8.0, 9.0, 10.0, 11.0],
        "peso_kg": [70.0, 77.0, 84.0, 93.0],
        "stance": ["Orthodox", "Southpaw", "Switch", "Orthodox"],
    })
    return pd.DataFrame(lutas), pd.DataFrame(historico), cadastro


def features_do_spec(spec):
    return list(spec["numericas"]) + list(spec["categoricas"])


class ConstruirBasePreLutaTests(unittest.TestCase):
    def setUp(self):
        self.lutas, self.hist, self.cadastro = criar_fixture()

    def construir(self, **kwargs):
        return construir_base_pre_luta(
            kwargs.get("lutas", self.lutas),
            kwargs.get("hist", self.hist),
            kwargs.get("cadastro", self.cadastro),
        )

    def test_estatisticas_e_resultado_correntes_nao_alteram_features(self):
        base, spec = self.construir()
        alteradas = self.lutas.copy(deep=True)
        for coluna in [
            "red_fighter_kd", "blue_fighter_kd",
            "red_fighter_sig_str_landed", "blue_fighter_sig_str_landed",
            "round", "time_seconds", "bonus",
            "red_fighter_pts_mean", "blue_fighter_pts_mean",
        ]:
            alteradas[coluna] = 99999
        alteradas["method"] = "KO/TKO"
        alteradas["red_fighter_result"] = self.lutas["blue_fighter_result"]
        alteradas["blue_fighter_result"] = self.lutas["red_fighter_result"]

        outra, outro_spec = self.construir(lutas=alteradas)
        self.assertEqual(spec, outro_spec)
        assert_frame_equal(base[features_do_spec(spec)], outra[features_do_spec(spec)])
        self.assertTrue((outra["alvo_red_vence"] == 1 - base["alvo_red_vence"]).all())

    def test_flag_restaura_ausencia_sem_apagar_zero_observado(self):
        hist = self.hist.copy(deep=True)
        data = self.lutas["event_date"].iloc[4]
        vermelho = hist["fighter_id"].eq("a") & hist["event_date"].eq(data)
        azul = hist["fighter_id"].eq("b") & hist["event_date"].eq(data)
        hist.loc[vermelho | azul, "kd_15min_antes"] = 0.0
        hist.loc[vermelho, "kd_15min_antes_sem_dado_antes"] = 0
        hist.loc[azul, "kd_15min_antes_sem_dado_antes"] = 1

        base, _ = self.construir(hist=hist)
        linha = base.loc[
            base["red_fighter_id"].eq("a") & base["event_date"].eq(data)
        ].iloc[0]
        self.assertEqual(linha["red_kd_15min_antes"], 0.0)
        self.assertTrue(pd.isna(linha["blue_kd_15min_antes"]))

    def test_conflito_no_mesmo_lutador_dia_e_rejeitado(self):
        conflito = self.hist.iloc[[8]].copy()
        conflito["sig_str_min_antes"] = 999.0
        hist = pd.concat([self.hist, conflito], ignore_index=True)
        with self.assertRaises(ValueError):
            self.construir(hist=hist)

    def test_ausencia_de_snapshot_exato_nao_usa_data_futura(self):
        data = self.lutas["event_date"].min()
        remover = self.hist["fighter_id"].eq("a") & self.hist["event_date"].eq(data)
        hist = self.hist.loc[~remover].copy()
        self.assertTrue((hist.loc[hist["fighter_id"].eq("a"), "event_date"] > data).all())
        with self.assertRaises(ValueError):
            self.construir(hist=hist)

    def test_snapshot_de_carreira_nao_entra_nas_features(self):
        base, spec = self.construir()
        cadastro = self.cadastro.copy(deep=True)
        for coluna in ["wins", "losses", "slpm", "peso_kg"]:
            cadastro[coluna] = 99999
        cadastro["stance"] = "Unknown"
        outra, outro_spec = self.construir(cadastro=cadastro)

        self.assertEqual(spec, outro_spec)
        features = features_do_spec(spec)
        assert_frame_equal(base[features], outra[features])
        for cor in ["red", "blue"]:
            for campo in ["wins", "losses", "slpm", "peso_kg", "stance"]:
                self.assertNotIn(f"{cor}_{campo}", features)

    def test_alvo_e_metadados_nao_sao_features(self):
        base, spec = self.construir()
        features = features_do_spec(spec)
        self.assertEqual(len(features), len(set(features)))
        for coluna in [
            "alvo_red_vence", "id_luta_pre_luta", "event_date",
            "red_fighter_id", "blue_fighter_id",
            "red_fighter_result", "blue_fighter_result",
            "red_fighter_kd", "round", "method", "bonus",
            "red_fighter_pts_mean", "blue_fighter_pts_mean",
        ]:
            self.assertNotIn(coluna, features)
        self.assertTrue(set(features).issubset(base.columns))
        self.assertTrue(any("grupo_temporal" in coluna for coluna in spec["categoricas"]))

    def test_construcao_nao_modifica_os_dataframes_de_entrada(self):
        originais = [dados.copy(deep=True) for dados in [self.lutas, self.hist, self.cadastro]]
        self.construir()
        for original, atual in zip(originais, [self.lutas, self.hist, self.cadastro]):
            assert_frame_equal(original, atual)

    def test_divisao_temporal_mantem_dias_inteiros(self):
        base, _ = self.construir()
        original = base.copy(deep=True)
        treino, teste, corte = dividir_temporal(base, fracao_teste=0.2)

        self.assertLess(treino["event_date"].max(), teste["event_date"].min())
        self.assertTrue((treino["event_date"] < corte).all())
        self.assertTrue((teste["event_date"] >= corte).all())
        self.assertTrue(set(treino["event_date"]).isdisjoint(teste["event_date"]))
        self.assertEqual(len(treino) + len(teste), len(base))
        for parte in [treino, teste]:
            self.assertTrue(parte.groupby("event_date").size().eq(2).all())
        assert_frame_equal(original, base)

    def test_periodo_de_calibracao_fica_fora_da_avaliacao(self):
        limite = self.lutas["event_date"].drop_duplicates().iloc[2]
        base, _ = construir_base_pre_luta(
            self.lutas, self.hist, self.cadastro, apos_calibracao=limite
        )
        self.assertTrue((base["event_date"] > limite).all())
        self.assertEqual(len(base), 6)

    def test_flag_invalida_nao_e_convertida_silenciosamente(self):
        hist = self.hist.copy(deep=True)
        hist.loc[0, "sig_str_min_antes_sem_dado_antes"] = 2
        with self.assertRaises(ValueError):
            self.construir(hist=hist)


if __name__ == "__main__":
    unittest.main()
