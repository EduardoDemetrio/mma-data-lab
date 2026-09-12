GUIA DE VARIÁVEIS DO PROJETO - UFC

OBSERVAÇÃO IMPORTANTE
---------------------
As variáveis abaixo estão apresentadas utilizando o prefixo "red_fighter_", referente ao lutador vermelho.

    As mesmas variáveis também existem para o lutador azul, utilizando o prefixo "blue_fighter_".



Exemplo:
red_fighter_name  -> lutador vermelho
blue_fighter_name -> lutador azul

Portanto, as definições abaixo são válidas tanto para RED quanto para BLUE.


*VARIÁVEIS (feito exemplo da variavel com lutador vermelho, porém só mudar a sintaxe)*

Estrutura:

Nome da variavel
- Descrição da variavel

=========

red_fighter_name
- Nome do lutador vermelho.

red_fighter_result
- Resultado do lutador vermelho (W/L).

red_fighter_kd
- Knockdown do lutador vermelho (Quantidade de golpes que leva o adversário ao chão).

red_fighter_sig_str
- Golpes em distancia como soco e chute e desses quantos foram significativos (acertaram).
        
red_fighter_sig_str_pct
- Percentual desses socos.
 
red_fighter_td
- Ação de takedown - basicamente tirar o oponente de pé para o chão de forma agarrada
  (e temos das chances quantas vezes conseguiram).

red_fighter_td_pct
- Ação de takedown em percentual.

red_fighter_sub_att
- Tentativas de finalização.

red_fighter_rev
- Quando um atleta sai da posição de solo (por baixo) e inverte para posição de cima
  (por cima do adversário).

red_fighter_ctrl
- Tempo de controle do seu adversário / domínio na posição.

red_fighter_sig_str_head
- Golpes significativos direcionados à cabeça ou seja golpes em situação de pé.

red_fighter_sig_str_body
- Golpes significativos direcionados no corpo ou seja golpes em situação de pé.

red_fighter_sig_str_leg
- Golpes significativos direcionados na perna ou seja golpes em situação de pé.

red_fighter_sig_str_distance
- Golpes significativos realizados à distância ou seja, fora das situações de clinch
  ou combate no solo.

red_fighter_sig_str_clinch
- Golpes significativos realizados durante o clinch.

red_fighter_sig_str_ground
- Golpes significativos realizados com a luta no solo.

red_fighter_sig_str_head_pct
- Percentual de acerto dos golpes significativos direcionados à cabeça.

red_fighter_sig_str_body_pct
- Percentual de acerto dos golpes significativos direcionados ao corpo.

red_fighter_sig_str_leg_pct
- Percentual de acerto dos golpes significativos direcionados à perna.

red_fighter_sig_str_distance_pct
- Percentual de acerto dos golpes significativos realizados à distância.

red_fighter_sig_str_clinch_pct
- Percentual de acerto dos golpes significativos realizados no clinch.

red_fighter_sig_str_ground_pct
- Percentual de acerto dos golpes significativos realizados no solo.

red_fighter_total_pts
- Total de pontos (Só existem casos de pontos se a luta NÃO for por nocaute).
- Total de pontos atribuídos ao lutador nos scorecards dos juízes.

red_fighter_sig_str_landed
- Quantidade de golpes significativos acertados.

red_fighter_sig_str_attempted
- Quantidade de golpes significativos tentados.

red_fighter_sig_str_pct_num
- Percentual de acerto dos golpes significativos convertido para formato numérico.

red_fighter_total_str_landed
- Quantidade total de golpes acertados.

red_fighter_total_str_attempted
- Quantidade total de golpes tentados.

red_fighter_td_landed
- Quantidade de takedowns realizados com sucesso.

red_fighter_td_attempted
- Quantidade de takedowns tentados.

red_fighter_td_pct_num
- Percentual de sucesso em takedowns convertido para formato numérico.
- **EXATAMENTE IGUAL red_fighter_td_pct**

red_fighter_sig_str_head_landed
- Golpes significativos na cabeça acertados.

red_fighter_sig_str_head_attempted
- Golpes significativos na cabeça tentados.

red_fighter_sig_str_body_landed
- Golpes significativos no corpo acertados.

red_fighter_sig_str_body_attempted
- Golpes significativos no corpo tentados.

red_fighter_sig_str_leg_landed
- Golpes significativos nas pernas acertados.

red_fighter_sig_str_leg_attempted
- Golpes significativos nas pernas tentados.

red_fighter_sig_str_distance_landed
- Golpes significativos à distância acertados.

red_fighter_sig_str_distance_attempted
- Golpes significativos à distância tentados.

red_fighter_sig_str_clinch_landed
- Golpes significativos no clinch acertados.

red_fighter_sig_str_clinch_attempted
- Golpes significativos no clinch tentados.

red_fighter_sig_str_ground_landed
- Golpes significativos no solo acertados.

red_fighter_sig_str_ground_attempted
- Golpes significativos no solo tentados.

red_key 
- Chave de identificação do lutador

red_odds,
- Odd geral do lutador vermelho para vencer a luta.

red_dec_odds
- Odd para o lutador vermelho vencer a luta por decisão dos juízes.

red_sub_odds
- Odd para o lutador vermelho vencer a luta por finalização.

red_ko_odds
- Odd para o lutador vermelho vencer a luta por nocaute ou nocaute técnico (KO/TKO)

red_match_weightclass_rank
- Ranking do lutador vermelho dentro da categoria de peso correspondente à luta.
- Variável que busca representar diretamente a posição do atleta no ranking da categoria
  em que aquele confronto está sendo disputado.
 
red_women_s_flyweight_rank
- Posição do lutador no ranking da categoria Women's Flyweight.

red_women_s_flyweight_rank
- Posição do lutador no ranking da categoria Women's Flyweight.

red_women_s_featherweight_rank
- Posição do lutador no ranking da categoria Women's Featherweight.

red_women_s_strawweight_rank
- Posição do lutador no ranking da categoria Women's Strawweight.

red_women_s_bantamweight_rank
- Posição do lutador no ranking da categoria Women's Bantamweight.

red_heavyweight_rank
- Posição do lutador no ranking da categoria Heavyweight.

red_light_heavyweight_rank
- Posição do lutador no ranking da categoria Light Heavyweight.

red_middleweight_rank
- Posição do lutador no ranking da categoria Middleweight.

red_welterweight_rank
- Posição do lutador no ranking da categoria Welterweight.

red_lightweight_rank
- Posição do lutador no ranking da categoria Lightweight.

red_featherweight_rank
- Posição do lutador no ranking da categoria Featherweight.

red_bantamweight_rank
- Posição do lutador no ranking da categoria Bantamweight.

red_flyweight_rank
- Posição do lutador no ranking da categoria Flyweight.

red_pound_for_pound_rank
- Posição do lutador no ranking Pound-for-Pound (P4P).
- Ranking que compara os principais lutadores independentemente da categoria de peso.

red_fighter_id
- Identificador único do lutador vermelho. 
 
event_date
- Data que o evento aconteceu

method
- Como foi que acabou a luta - sendo um nocaute ou por pontuação

time_format 
- Qual é formato de tempo da luta
- Temos lutas de 3 rounds e de 5 rounds (geralmente lutas principais do dia)

bout_type
- Categoria da luta, basicamente a divisão dos lutadores que é realizado por pesos

bonus
- Se essa luta recebeu bonus

event_name
- Nome do evento em sua grande maioria os eventos tem nomes das lutas principais ou uma numeração que pode indicar eventos com mais de duas lutas principais

event_location
- Localização do evento, o que tem a possibilidade de o lutador está lutando em seu pais, cidade 
- geralmente está como Cidade,Estado,Pais 

country
- Pais do evento

time_seconds 
 - Tempo da duração das lutas em segundos

better_rank
- Quem está melhor rankeado entre os dois lutadores
