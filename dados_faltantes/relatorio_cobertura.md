# Relatório de cobertura — lutadores

Consulta: 24/10/2026.

- Lutadores pesquisados nominalmente na ESPN: **2.485 de 2.485 (100%)**.
- Lutadores com novos dados: **1856**.
- Campos vazios preenchidos com fonte: **4585**.
- Campos ainda nulos: **3735**.
- Preenchimento dos seis campos: **44.20% → 74.95%**.

## Cobertura por campo

| Campo | Antes | Adicionados | Depois | Nulos restantes | Cobertura final |
| --- | ---: | ---: | ---: | ---: | ---: |
| sexo | 586 | 1637 | 2223 | 262 | 89.46% |
| categoria_principal | 654 | 1316 | 1970 | 515 | 79.28% |
| date_of_birth | 2088 | 8 | 2096 | 389 | 84.35% |
| peso_kg | 654 | 1188 | 1842 | 643 | 74.12% |
| height_cm | 2116 | 132 | 2248 | 237 | 90.46% |
| reach_cm | 492 | 304 | 796 | 1689 | 32.03% |

## Método e fontes

Cada nome foi procurado no mecanismo público da ESPN ou ligado a um identificador ESPN por correspondência nominal única em um índice histórico. Os valores foram obtidos novamente no cadastro público atual da ESPN, e não copiados do índice histórico. A associação exige nome coincidente, ignorando acentos, espaços e pontuação. Havendo data de nascimento em ambas as fontes, ela deve coincidir exatamente. Homônimos só foram resolvidos quando uma única data de nascimento coincidia com o CSV. Mudanças de nome só foram aceitas quando o mesmo ID ESPN tinha vínculo histórico com o nome original e nascimento coincidente.

O site oficial do UFC foi consultado para lacunas adicionais de categoria, peso, altura e envergadura. Apenas páginas cujo nome de perfil coincidiu com o nome original foram utilizadas. Redirecionamentos para buscas ou páginas sem perfil não foram tratados como evidência. Registros com conflito de identidade na ESPN não foram preenchidos automaticamente pelo UFC.

As URLs exatas que fundamentam cada inclusão estão em `fonte_<campo>_url`. Para a ESPN, elas apontam ao cadastro público estruturado que contém o valor. `fonte_perfil_url` fornece o perfil de leitura. `fontes_urls` reúne as fontes efetivamente usadas na linha. Fontes vazias em campos preexistentes significam que o valor foi preservado, sem atribuir a ele uma nova verificação.

Conversões: 1 libra = 0,45359237 kg; 1 polegada = 2,54 cm. O peso corresponde ao peso cadastrado, e não necessariamente à última pesagem. A categoria é a declarada pela fonte, sem dedução a partir do peso. Data de nascimento não foi calculada pela idade. Sexo foi preenchido apenas a partir de um campo explícito da fonte ou de uma divisão explicitamente feminina. Valores zero e marcadores de ausência não foram usados para completar medidas.

Os IDs, nomes, ordem das linhas e todos os valores previamente preenchidos foram preservados. Os nulos permanecem como campos vazios, conforme o CSV original. Codificação dos CSVs: UTF-8 com BOM; delimitador vírgula; decimais com ponto; datas AAAA-MM-DD.

## Resultado da identificação na ESPN

| Situação | Lutadores |
| --- | ---: |
| identidade_confirmada | 2237 |
| nao_localizado | 126 |
| data_nascimento_divergente | 84 |
| nome_ambiguo | 28 |
| altura_divergente_sem_nascimento | 5 |
| erro_acesso | 2 |
| homonimo_sem_dados_para_distinguir | 1 |
| nome_divergente | 1 |
| homonimo_incompativel | 1 |

## Consultas complementares ao UFC

| Situação | Lutadores |
| --- | ---: |
| identidade_confirmada | 1133 |
| erro_acesso | 376 |
| perfil_nao_confirmado | 170 |

Inclusões por fonte: ESPN 4450; UFC 135.

## Limites da cobertura

Pesquisa nominal não equivale a preenchimento total. Ausência de resultado nesta pesquisa não prova que o dado não exista na internet. Nulos podem resultar de cadastro sem o campo, nome não localizado, homônimos, divergência de nascimento ou falha de acesso. As situações sem associação segura estão listadas em `pendencias_identificacao.csv`. Não se corrigiram datas, medidas nem rótulos já existentes, inclusive categorias antigas que mencionam títulos de torneios. As contagens de preenchimento incluem esses valores originais, sem afirmar que todos foram revalidados.

## Arquivos

- `lutadores_revisados.csv`: CSV integral revisado e fontes por campo.
- `cobertura_por_campo.csv`: tabela de cobertura antes e depois.
- `preenchimentos_verificados.csv`: uma linha por inclusão, com valor e fonte.
- `pendencias_identificacao.csv`: casos sem associação segura na ESPN.

Validação: 2.485 linhas preservadas, IDs únicos, valores preexistentes intactos, fonte presente em cada novo preenchimento e nenhuma substituição de nulo por zero.

## Verificações adicionais de identidade e coerência

Nos registros sem nascimento, diferenças de altura superiores a 5,08 cm entre CSV e ESPN impediram inclusões automáticas. Os casos Adam Smith e Ryan Parker também foram retidos por homonímia. Para Ryan Parker, a participação no UFC 7 em 1995 é incompatível com o nascimento em 1992 do perfil ESPN encontrado. Esses vínculos foram excluídos das inclusões. Medidas ausentes, zero ou fora de faixas amplas de plausibilidade permaneceram nulas. Essas faixas servem apenas para rejeitar valores, nunca para estimá-los.

Referências para a revisão de homônimos: [Ryan Parker no UFC](https://www.ufc.com/athlete/nissen-osternek-3) e [outro Adam Smith no Sherdog](https://www.sherdog.com/fighter/Adam-Smith-25024). O [índice histórico de nomes ESPN](https://gist.github.com/a1ip/d30592f4199082fd851807e5c0e48ea0) foi usado somente para localizar identificadores e vínculos de nomes antigos, sem aproveitar seus valores antigos para preencher campos.

Consultas complementares a URLs do UFC: 1679. Perfis com nome coincidente: 1133. A existência de um perfil não significa que ele tenha dados úteis para as lacunas do CSV.
