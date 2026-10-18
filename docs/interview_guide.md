# Roteiro para explicar o projeto

Este guia é material de estudo. Apresente apenas as partes que você consegue executar e explicar; não descreva o laboratório como trabalho entregue a uma empresa.

## Apresentação em 60 segundos

“Montei um laboratório reproduzível de análise de varejo com Python e SQL. Começo com dados simulados, valido contratos e construo fatos em grãos separados de pedido e item. Depois analiso receita, margem, retenção e segmentos RFM. A pergunta principal é se um desconto que melhora conversão também melhora contribuição. No experimento simulado, a conversão aumenta, mas o resultado por cliente sorteado cai. Documentei as hipóteses, os limites e os testes para explicar por que eu não expandiria esse desconto nesse cenário.”

## Perguntas que você precisa responder

1. **Por que SQLite?** Execução local sem credenciais, baixo custo e SQL inspecionável. Não foi escolhido para mostrar escala distribuída. Para produção, avaliar banco/plataforma, concorrência, volume, SLA e segurança.
2. **Onde entra pandas?** Leitura dos arquivos, limpeza, validações, coortes, RFM e tabelas do relatório. SQL concentra os fatos e as métricas financeiras. NumPy gera as simulações e reamostragens; SciPy faz a inferência.
3. **Por que separar pedido e item?** O custo logístico pertence ao pedido. Um join ingênuo com vários itens multiplica esse custo.
4. **Como trata duplicatas?** Remove apenas cópias idênticas, conta as remoções e interrompe diante de chaves repetidas com conteúdo diferente.
5. **O que significa idempotência aqui?** O mesmo snapshot reconstruído não duplica pedidos. Não há ingestão incremental nem checkpoint de API.
6. **Por que contribuição por sorteado?** Inclui o efeito em quem compra e em quem não compra. Evita selecionar apenas compradores após o tratamento.
7. **Por que Welch?** Compara médias de grupos independentes sem assumir variâncias iguais. O desfecho tem zeros e assimetria; há muitos clientes e o bootstrap avalia sensibilidade. Isso não substitui investigação de dependência ou contaminação em produção.
8. **O que significa o IC?** É um intervalo produzido por um procedimento com cobertura nominal de 95% em repetições sob as premissas. Não é “95% de chance de este intervalo conter a verdade”.
9. **Por que não preencher a coorte incompleta com zero?** Ainda não observamos a janela inteira. Zero confundiria ausência de observação com ausência de recompra.
10. **O desconto causou o pico de novembro?** A série histórica não permite essa conclusão. O experimento é outra população simulada, com sorteio independente.
11. **O que está faltando para produção?** Ingestão real, contratos com evolução de esquema, monitoramento operacional, controle de concorrência, testes de exposição/aleatorização, poder estatístico, autorização, implantação e observabilidade. Airflow não é dependência deste laboratório.
12. **Qual foi o papel da IA?** Houve assistência de IA na elaboração do código e da documentação. O repositório torna implementação, resultados e testes inspecionáveis; estudar e validar faz parte do uso do projeto.

## Exercícios antes da entrevista

- Execute o pipeline e localize os 20 registros duplicados na origem e no relatório de qualidade.
- Abra `warehouse.sql` e explique cada CTE/agrupamento; reconcilie uma compra manualmente.
- Altere o desconto em `generate_experiment`, execute novamente e explique o efeito. Restaure o código e a seed original antes de comparar com o snapshot publicado.
- Execute os testes e injete um `product_id` inexistente para observar a falha de qualidade.
- Explique em inglês: “Conversion increased, but contribution per randomized customer fell. I would not roll out the discount under these simulated conditions.”
