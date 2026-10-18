# Desenho do experimento

## Pergunta e estimando

Oferecer 15% de desconto aumenta a **contribuição média por cliente sorteado** em uma janela fixa de 14 dias?

Este é um desenho simulado especificado no código. Não houve experimento com clientes reais. Não há pré-registro externo: a expressão “métrica primária predefinida” descreve o contrato analítico do laboratório, não uma alegação de pesquisa registrada.

## Plano

| Decisão | Definição |
|---|---|
| Unidade de aleatorização/análise | Cliente; uma linha por cliente |
| Alocação esperada | 50/50, sorteio independente com NumPy |
| Controle | Sem incentivo |
| Tratamento | 15% de desconto |
| Amostra didática | 16.000 clientes; sem cálculo de poder prévio |
| Janela | 14 dias completos por cliente, agregados pelo gerador |
| Métrica primária | Receita após desconto menos CMV e logística, por cliente sorteado |
| População analisada | Todos os sorteados; não compradores recebem zero |
| Hipótese nula | Diferença de médias igual a zero |
| Inferência principal | Welch bilateral; alfa 5%; IC 95% da diferença tratamento − controle |
| Sensibilidade | Bootstrap percentil por cliente, dentro de cada braço; 1.000 reamostragens |
| Checagem de alocação | Qui-quadrado de contagens; bloquear inferência se SRM p < 0,001 |
| Conversão | Diagnóstico descritivo secundário, sem segundo teste confirmatório |

## Por que o denominador importa

Lucro por comprador compara grupos cuja composição foi modificada pelo próprio desconto. A pergunta comercial é o que acontece com todos os clientes elegíveis expostos à política. Por isso, a média usa todos os sorteados, inclusive resultados zero. A mesma unidade é preservada no bootstrap.

## Regra didática de decisão

- IC inteiro abaixo de zero: não expandir o desconto.
- IC inteiro acima de zero: avaliar expansão considerando guardrails e viabilidade econômica.
- IC cruzando zero: resultado inconclusivo.

Um IC positivo não dispensa efeito mínimo relevante, custos de implementação, guardrails ou validação operacional. Em produção, definir esses critérios antes da execução. Um p-valor baixo não mede tamanho do impacto nem probabilidade de a hipótese nula ser verdadeira.

## Como a simulação funciona

O controle tem probabilidade programada de compra de 21%; o tratamento, 27%. O valor bruto da compra segue uma lognormal, com os mesmos parâmetros nos dois braços. CMV equivale a 68% do valor bruto, logística custa R$ 10 por compra, e o desconto reduz somente a receita do tratamento. Estes parâmetros **já embutem** o mecanismo de perda de contribuição. O caso demonstra como detectar e explicar isso, não descobre um padrão desconhecido em dados reais.

O SRM verifica apenas se as contagens são incompatíveis com o plano; não comprova aleatorização correta nem ausência de contaminação. Não há logs de exposição, timestamps por cliente, perdas de acompanhamento, devoluções, interferência, efeitos de repetição ou custos de aquisição. A janela de 14 dias é uma premissa do gerador, não uma validação temporal extraída de eventos.

O conjunto histórico é independente do experimento. Seu pico de novembro não é uma estimativa causal: sazonalidade e desconto variam simultaneamente.

## Referências técnicas

- [SciPy — teste de médias independentes e opção de Welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html)
- [pandas — joins, merge e concatenação](https://pandas.pydata.org/docs/user_guide/merging.html)
- [SQLite — atomicidade de commits](https://www.sqlite.org/atomiccommit.html). A substituição de snapshots deste projeto usa um arquivo temporário e `os.replace`, além das transações internas do SQLite.
