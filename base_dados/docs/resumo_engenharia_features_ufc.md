# Resumo da estrutura de dados para engenharia de features UFC

Este documento registra o estado atual da investigacao das bases e os proximos passos para continuar a construcao do dataset preditivo do TCC.

## Objetivo atual

Estamos na etapa de engenharia de features, que e o topico central do TCC. A ideia e construir uma base preditiva temporal, usando apenas informacoes disponiveis antes de cada luta para prever o resultado.

## Estrutura definida

```text
fighters_dim_final
        ↓
dimensao consolidada de lutadores

merged_stats_n_scorecards
        ↓
base central de lutas

fight_stats
        ↓
historico granular por round

ultimate_ufc_dataset/ufc_master
        ↓
odds e features externas de mercado/contexto
```

## Tabelas e papel de cada uma

### `fighters_dim_final`

Tabela consolidada a partir da uniao entre:

- `fighter_tott`
- `raw_fighter_details`

O objetivo e ter uma dimensao unica de lutadores, com identificador, nome normalizado e atributos fisicos/cadastrais.

Principais usos:

- centralizar `fighter_id`;
- completar lutadores ausentes em uma das fontes;
- adicionar atributos como altura, peso, envergadura, stance e data de nascimento;
- apoiar joins com as tabelas de lutas.

Quando o lutador existe em `fighter_tott`, o ideal e manter o ID extraido da URL do UFCStats. Quando ele existe apenas em `raw_fighter_details`, pode ser criado um ID interno distinto.

### `merged_stats_n_scorecards`

Sera a base central do projeto.

Ela representa uma luta por linha, com lutador vermelho, lutador azul, evento, data, resultado, estatisticas finais da luta e scorecards.

Status atual:

- agora tem conexao com `fighters_dim_final`;
- deve receber `red_fighter_id` e `blue_fighter_id`;
- sera usada para reconstruir o historico de lutas por lutador.

Importante: para modelagem preditiva, as estatisticas da propria luta nao devem entrar diretamente como features da mesma linha, pois representam informacao pos-luta. Elas devem ser usadas para calcular historico anterior do atleta.

### `fight_stats`

Base granular por luta, lutador e round.

Ela sera usada para criar features historicas mais refinadas, olhando o comportamento do lutador ao longo dos rounds.

Ideias de features:

- media de rounds por luta do lutador;
- media de golpes significativos acertados por round;
- volume de golpes no inicio da luta;
- queda de desempenho nos rounds finais;
- sinais de cansaco ao longo da luta;
- media de quedas tentadas e quedas aplicadas;
- media de tempo de controle;
- desempenho recente nas ultimas N lutas;
- diferenca entre desempenho no round 1 e nos rounds seguintes.

Essa tabela deve alimentar uma camada intermediaria no formato:

```text
1 linha = 1 lutador em 1 luta/round
```

Depois, as features historicas devem ser agregadas para voltar ao formato final:

```text
1 linha = 1 luta
```

### `ultimate_ufc_dataset/ufc_master`

Fonte auxiliar importante para enriquecer a base central.

Proximo passo: criar uma chave entre `ufc_master` e `merged_stats_n_scorecards`.

O principal interesse nessa tabela sao as odds e informacoes de mercado, que podem indicar fatores como expectativa externa, popularidade, fase percebida do lutador e favoritismo antes da luta.

Colunas de interesse:

- `red_odds`
- `blue_odds`
- `red_ev`
- `blue_ev`
- `red_dec_odds`
- `blue_dec_odds`
- `red_sub_odds`
- `blue_sub_odds`
- `red_ko_odds`
- `blue_ko_odds`
- `title_bout`
- `weight_class`
- `gender`
- `no_of_rounds`

Colunas pos-luta, como `winner`, `finish`, `finish_round`, `finish_round_time` e `total_fight_time_secs`, nao devem entrar como features preditivas.

## Proximos passos

1. Finalizar e validar a `fighters_dim_final`.
2. Garantir que `merged_stats_n_scorecards` tenha `red_fighter_id` e `blue_fighter_id`.
3. Criar uma chave confiavel de luta para a `merged_stats_n_scorecards`.
4. Quebrar a base central em formato historico por lutador.
5. Usar `fight_stats` para gerar features temporais por round.
6. Reagrupar as features para o formato final de uma linha por luta.
7. Criar chave entre `merged_stats_n_scorecards` e `ultimate_ufc_dataset/ufc_master`.
8. Adicionar odds e metadados pre-luta como features auxiliares.
9. Separar claramente features pre-luta de informacoes pos-luta para evitar vazamento temporal.

## Observacao metodologica

O ponto mais importante e garantir que, para cada luta, as features usadas pelo modelo representem apenas informacoes disponiveis antes daquela luta acontecer.

As estatisticas da luta atual podem ser usadas para atualizar o historico do lutador nas lutas futuras, mas nao podem ser usadas para prever a propria luta em que foram registradas.
