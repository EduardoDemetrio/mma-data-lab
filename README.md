# MMA Data Lab

Projeto de TCC voltado para coleta, padronizacao e analise de dados historicos de lutas de MMA, com foco inicial em eventos do UFC.

O objetivo principal e construir uma base preditiva temporal, usando apenas informacoes disponiveis antes de cada luta para apoiar modelos de previsao de resultado.

## Objetivo

Este projeto busca organizar diferentes fontes de dados sobre lutas, lutadores, eventos, estatisticas e odds em uma estrutura unica para analise e modelagem.

A ideia central e transformar dados brutos em bases confiaveis para responder perguntas como:

- quais caracteristicas historicas ajudam a explicar o resultado de uma luta;
- como comparar o desempenho recente de dois lutadores;
- como evitar vazamento de informacao ao criar features preditivas;
- qual o impacto de variaveis como odds, categoria, idade, alcance, postura e historico recente.

## Estrutura do projeto

```text
.
+-- explorando_dados.ipynb
+-- aula/
+-- base_dados/
|   +-- processed_bronze/
|   +-- processed_silver/
|   +-- docs/
+-- README.md
```

## Principais pastas

- `explorando_dados.ipynb`: notebook de exploracao das fontes de dados.
- `base_dados/processed_bronze/`: primeira camada padronizada dos dados.
- `base_dados/processed_silver/`: bases consolidadas usadas para analise e engenharia de features.
- `base_dados/docs/`: documentacao auxiliar sobre estrutura, qualidade e proximos passos.
- `aula/`: materiais de apoio e apresentacoes do TCC.

## Fontes de dados investigadas

O projeto utiliza e compara diferentes bases relacionadas a lutas de MMA/UFC:

- `UFC-DataLab`: fonte de referencia para pipeline, estatisticas e scorecards.
- `scrape_ufc_stats`: referencia para coleta incremental de dados do UFCStats.
- `ultimate_ufc_dataset`: dataset enriquecido com odds, rankings e features historicas.
- `ufc-stats-crawler`: referencia tecnica de crawler Scrapy.
- datasets Kaggle de UFC: bases complementares para comparacao e enriquecimento.

## Bases consolidadas

Atualmente, a camada `processed_silver` contem duas bases principais:

- `dim_fighters.csv`: dimensao consolidada de lutadores, com atributos fisicos, identificadores e estatisticas gerais.
- `dim_fight.csv`: base consolidada de lutas, eventos, resultados, estatisticas, scorecards e variaveis auxiliares como odds.

Essas bases servem como ponto de partida para a proxima etapa: engenharia de features temporais.

## Pipeline de dados

Os scripts principais ficam em:

```text
base_dados/processed_bronze/codigos_python/
```

Para rodar todo o pipeline bronze e silver:

```bash
python base_dados/processed_bronze/codigos_python/rodar_pipeline_bronze_silver.py
```

Esse comando executa:

1. padronizacao das fontes brutas para a camada bronze;
2. geracao da camada silver;
3. relatorios de qualidade das tabelas processadas.

## Metodologia

O principal cuidado metodologico do projeto e evitar vazamento temporal.

Isso significa que, para prever uma luta, o modelo deve usar somente informacoes que estavam disponiveis antes dela acontecer. Estatisticas da propria luta podem ser usadas para atualizar o historico dos lutadores em lutas futuras, mas nao devem ser usadas como entrada para prever a mesma luta.

## Status

Projeto em desenvolvimento como parte do TCC.

As etapas de investigacao, organizacao das fontes e construcao das primeiras camadas de dados ja foram iniciadas. A proxima etapa principal e a engenharia de features temporais para modelagem preditiva.
