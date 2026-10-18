# Contrato de dados e métricas

Todos os registros são simulados. Não há nomes, e-mails, documentos nem dados corporativos.

## Entradas

| Arquivo | Grão e chave | Campos relevantes |
|---|---|---|
| `customers.csv` | Uma linha por cliente; `customer_id` | Região sintética |
| `products.csv` | Uma linha por produto; `product_id` | Categoria, preço e custo de referência |
| `orders.csv` | Uma linha por pedido; `order_id` | Cliente, data, status, custo logístico |
| `order_items.csv` | Uma linha por item; `item_id` | Pedido, produto, quantidade, preço/custo na venda, desconto |
| `experiment.csv` | Uma linha por cliente sorteado; `customer_id` | Variante, conversão, receita, CMV, logística, contribuição |

No histórico, há 6.000 clientes possíveis, 24 produtos e 24.000 pedidos únicos. O arquivo bruto de pedidos inclui 20 cópias idênticas inseridas intencionalmente para exercitar a deduplicação. Clientes sem compras não aparecem no RFM. IDs do experimento e do histórico pertencem a populações independentes: **não devem ser relacionados**, mesmo que os números coincidam.

## Camada analítica SQLite

| Objeto | Grão | Uso |
|---|---|---|
| `dim_customer` | Cliente | Região e relacionamento |
| `dim_product` | Produto | Categoria |
| `fct_order_item` | Item | Receita e CMV em centavos inteiros |
| `fct_order` | Pedido | Receita, CMV, logística e contribuição |
| `mart_monthly` | Mês | Vendas, compradores, ticket e margem |
| `mart_category` | Categoria | Receita, lucro bruto e margem bruta |

A agregação dos itens ocorre **antes** de acrescentar a logística do pedido. Somar custos de pedido depois de um join com várias linhas de itens causaria dupla contagem. O teste de reconciliação protege esse caso.

## Regras financeiras

- Receita líquida do item: `quantidade × preço × (1 − desconto)`, arredondada para centavos; somente pedidos entregues.
- CMV: `quantidade × custo unitário`, somente pedidos entregues.
- Contribuição do pedido: `receita líquida − CMV − custo logístico`.
- Margem de contribuição: `soma das contribuições / soma da receita líquida`; **não** é a média das margens de cada pedido.
- Ticket médio: `receita líquida / pedidos entregues`.
- Margem bruta por categoria: `(receita − CMV) / receita`; exclui logística.
- Devolução: receita e CMV zerados, estoque integralmente recuperado; logística permanece. Cancelamento: tudo zerado. Estas são simplificações do caso didático.
- Impostos, custos fixos e aquisição não entram; contribuição não deve ser chamada de lucro líquido.
- O SQL faz o arredondamento financeiro por item antes da agregação. Valores de entrada usam decimal em CSV; fatos usam centavos inteiros.

## Coortes e RFM

- Coorte: mês da primeira compra entregue observada em 2025, não necessariamente da primeira compra da vida do cliente.
- Retenção M1: compradores da coorte que compraram no mês seguinte / tamanho da coorte. Não exige compra em todos os meses intermediários.
- M0 vale 100% em meses completos. Janelas futuras ou meses parcialmente observados ficam ausentes, não zero.
- A série fecha em `2025-12-31`; RFM é calculado em `2026-01-01`, sem compras futuras.
- Segmentação RFM é heurística: recentes frequentes = recência ≤ 60 dias e frequência ≥ 4; inativos = recência > 120 dias; demais = outros. O valor monetário também é exportado. Não há modelo preditivo de churn nem validação de propensão.

## Validações e carregamento

Falham: colunas ausentes, nulos obrigatórios, números não finitos, IDs/quantidades não inteiros ou não positivos, valores financeiros negativos na origem, desconto fora de `[0,1]`, datas inválidas, status desconhecidos, referências quebradas, pedidos sem itens e chaves duplicadas com conteúdo divergente. Cópias completamente idênticas são removidas e contadas.

O carregamento reconstrói um snapshot em banco temporário e troca o arquivo final com `os.replace` somente após sucesso. Reexecuções não acrescentam os mesmos pedidos. A estratégia é **carga completa**, não CDC nem incremental. É adequada para demonstração local com um único processo, não garante concorrência entre várias execuções e não equivale a uma plataforma distribuída. Falhas na reconstrução preservam o banco anterior; os relatórios são sobrescritos separadamente após o banco, sem transação única de toda a pasta.
