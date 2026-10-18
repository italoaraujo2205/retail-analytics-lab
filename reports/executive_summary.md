# Relatorio executivo

**Dados integralmente simulados. Valores monetarios em BRL.** Esta demonstracao nao estima resultados de uma empresa real.

## A decisao

**Nao expandir o desconto.** O desconto elevou a conversao de 20.36% para 26.81% (+6.45 pontos percentuais), mas a contribuicao media por cliente sorteado passou de R$ 13,61 para R$ 8,00.

O efeito estimado na metrica primaria foi **R$ -5,61 por cliente**, com IC 95% de [R$ -6,36; R$ -4,86], teste de Welch p = 1.17292e-47. O intervalo bootstrap foi [R$ -6,37; R$ -4,90]. Sao 7888 clientes no controle e 8112 no tratamento; teste de balanceamento da alocacao (SRM) p = 0.0766.

## Contexto operacional

- Receita liquida anual: **R$ 16.424.057,66**.
- Contribuicao apos CMV e custo de atendimento/logistica: **R$ 5.305.344,41**, margem de **32.30%**.
- Pedidos entregues: **22075**.
- Duplicatas identicas de pedidos removidas: **20**.

![Visao geral](figures/overview.svg)

## Interpretacao e proximas acoes

1. Conversao e um diagnostico secundario, nao a regra de aprovacao do experimento. O desconto custa margem nas compras que aconteceriam mesmo sem incentivo.
2. A serie historica e observacional. Nao atribuir o pico de novembro causalmente ao desconto: sazonalidade e promocao foram inseridas juntas no gerador.
3. Antes de um teste real, estimar tamanho da amostra com variancia historica e efeito minimo economicamente relevante; fixar horizonte e metrica primaria. Este laboratorio usa amostra didatica, sem calculo de poder previo.
4. Testar incentivos menores ou segmentados exigiria um novo experimento. As coortes e os segmentos RFM ajudam a formular hipoteses; nao comprovam que uma campanha funciona.

## Limites

- Experimento independente da base historica, um registro por cliente e janela fixa simulada de 14 dias. Inclui nao compradores com resultado zero (intention-to-treat).
- A simulacao possui efeito de desconto definido no codigo. Significancia estatistica aqui demonstra o metodo; nao valida impacto comercial real.
- Contribuicao nao e lucro liquido: impostos, despesas fixas, aquisicao e efeitos de longo prazo nao entram no modelo.
- Na base historica, devolucoes recuperam integralmente o estoque e mantem o custo logistico. Devolucoes parciais e atrasadas nao sao modeladas.
- Os resultados se referem ao ano de 2025; coortes incompletas recebem valor ausente, nao zero.
- Sem monitoramento sequencial ou multiplas metricas primarias. Nao interpretar a comparacao de conversao como um segundo teste confirmatorio.
