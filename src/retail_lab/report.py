"""Small, dependency-free SVG/HTML report with the same metric definitions as SQL."""
import html
import json
from pathlib import Path

import pandas as pd


def money(value: float) -> str:
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def overview(monthly: pd.DataFrame, categories: pd.DataFrame, cohorts: pd.DataFrame, experiment: dict) -> str:
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="850" viewBox="0 0 1200 850" role="img" aria-labelledby="title desc">',
             '<title id="title">Retail Analytics Lab</title><desc id="desc">Dados simulados. Receita mensal, margem por categoria, retencao e experimento de desconto.</desc>',
             '<style>text{font-family:Arial,sans-serif;fill:#dce8f4}.muted{fill:#9eafc1}.small{font-size:12px}.heading{font-size:18px;font-weight:700}</style>',
             '<rect width="1200" height="850" rx="20" fill="#0b1320"/>']
    def text(x, y, value, size=14, cls="", anchor="start"):
        color = "#9eafc1" if cls == "muted" else "#dce8f4"
        weight = "700" if cls == "heading" else "400"
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-family="DejaVu Sans,Arial,sans-serif" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{html.escape(str(value))}</text>')
    def rect(x, y, w, h, fill, radius=3):
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" rx="{radius}"/>')
    text(34, 42, "RETAIL ANALYTICS LAB", 26, "heading")
    text(34, 67, "Mais conversao significa mais lucro?", 17)
    text(1160, 42, "SIMULACAO | 2025 | BRL", 12, "muted", "end")
    total_revenue = monthly.net_revenue.sum()
    total_profit = monthly.contribution.sum()
    cards = [("RECEITA LIQUIDA", money(total_revenue)), ("CONTRIBUICAO", money(total_profit)), ("MARGEM DE CONTRIBUICAO", f"{total_profit / total_revenue:.1%}"), ("PEDIDOS ENTREGUES", f"{int(monthly.delivered_orders.sum()):,}".replace(",", "."))]
    for i, (label, value) in enumerate(cards):
        x = 30 + i * 290
        rect(x, 92, 272, 80, "#152235", 9)
        text(x + 15, 117, label, 11, "muted")
        text(x + 15, 149, value, 23)
    for x, y in [(30, 194), (620, 194), (30, 507), (620, 507)]:
        rect(x, y, 550, 293 if y == 194 else 313, "#111e30", 9)
    text(50, 224, "Receita por mes", 18, "heading")
    text(50, 244, "Promocoes e sazonalidade foram simuladas.", 12, "muted")
    max_revenue = monthly.net_revenue.max()
    for i, row in enumerate(monthly.itertuples(index=False)):
        x = 54 + i * 42
        height = 175 * row.net_revenue / max_revenue
        rect(x, 446 - height, 27, height, "#62d4c0" if row.month[-2:] != "11" else "#f6b96b")
        text(x + 13, 466, row.month[-2:], 11, "muted", "middle")
    text(54, 482, f"Pico: {money(max_revenue)} | eixo vertical com origem zero", 11, "muted")
    text(642, 224, "Margem bruta por categoria", 18, "heading")
    text(642, 244, "Receita menos CMV; exclui logistica.", 12, "muted")
    for i, row in enumerate(categories.sort_values("gross_margin", ascending=False).itertuples(index=False)):
        y = 278 + i * 50
        text(642, y + 15, row.category, 13)
        rect(758, y, max(0, row.gross_margin) * 700, 22, "#7ea7fa")
        text(1147, y + 16, f"{row.gross_margin:.1%}", 13, anchor="end")
    text(642, 482, "Barras: escala de 0% a 50%", 11, "muted")
    text(50, 537, "Retencao por coorte", 18, "heading")
    text(50, 558, "Compra no mes; janelas incompletas ficam cinza.", 12, "muted")
    cohort_list = sorted(cohorts.cohort.unique())[-6:]
    for age in range(4):
        text(230 + age * 88, 583, f"M{age}", 12, "muted", "middle")
    for i, cohort in enumerate(cohort_list):
        y = 596 + i * 30
        text(52, y + 18, cohort, 12)
        for age in range(4):
            v = cohorts.loc[(cohorts.cohort == cohort) & (cohorts.age_month == age), "retention"].iloc[0]
            fill = "#263345" if pd.isna(v) else f"rgb({int(28 + 20 * v)},{int(70 + 105 * v)},{int(92 + 75 * v)})"
            rect(190 + age * 88, y, 80, 25, fill)
            text(230 + age * 88, y + 17, "--" if pd.isna(v) else f"{v:.0%}", 12, anchor="middle")
    text(50, 801, "M0 = mes da primeira compra; nao equivale a churn.", 11, "muted")
    text(642, 537, "Desconto de 15%: teste A/B", 18, "heading")
    text(642, 558, "Metrica primaria: contribuicao por cliente sorteado.", 12, "muted")
    for i, (name, label) in enumerate([("control", "Controle"), ("discount", "Desconto")]):
        group = experiment["groups"][name]
        y = 588 + i * 66
        text(642, y + 15, label, 14)
        rect(748, y, group["mean_contribution"] * 19, 24, "#62d4c0" if i == 0 else "#f6b96b")
        text(1137, y + 16, money(group["mean_contribution"]), 14, anchor="end")
        text(748, y + 43, f"Conversao: {group['conversion']:.1%} | n = {group['n']}", 12, "muted")
    text(642, 740, f"Efeito: {money(experiment['difference'])} por cliente", 16)
    low, high = experiment["ci_95"]
    text(642, 764, f"IC 95%: [{money(low)}; {money(high)}]", 13, "muted")
    text(642, 795, experiment["decision"], 17, "heading")
    parts.append('</svg>')
    return "\n".join(parts)


def write_reports(root: Path, monthly: pd.DataFrame, category: pd.DataFrame, cohort: pd.DataFrame, rfm: pd.DataFrame, experiment: dict, audit: dict, manifest: dict) -> None:
    out = root / "reports"
    (out / "figures").mkdir(parents=True, exist_ok=True)
    for name, frame in [("monthly", monthly), ("category", category), ("cohorts", cohort)]:
        frame.to_csv(out / f"{name}.csv", index=False)
    rfm_summary = rfm.groupby("segment").agg(customers=("customer_id", "count"), average_recency=("recency_days", "mean"), average_frequency=("frequency", "mean"), revenue=("monetary", "sum")).round(2).reset_index()
    rfm_summary.to_csv(out / "rfm_summary.csv", index=False)
    for name, obj in [("experiment", experiment), ("data_quality", audit), ("manifest", manifest)]:
        (out / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    svg = overview(monthly, category, cohort, experiment)
    (out / "figures" / "overview.svg").write_text(svg, encoding="utf-8")
    control, treatment = experiment["groups"]["control"], experiment["groups"]["discount"]
    low, high = experiment["ci_95"]
    contribution = monthly.contribution.sum()
    revenue = monthly.net_revenue.sum()
    summary = f"""# Relatorio executivo

**Dados integralmente simulados. Valores monetarios em BRL.** Esta demonstracao nao estima resultados de uma empresa real.

## A decisao

**{experiment['decision']}.** O desconto elevou a conversao de {control['conversion']:.2%} para {treatment['conversion']:.2%} ({experiment['conversion_difference_pp']:+.2f} pontos percentuais), mas a contribuicao media por cliente sorteado passou de {money(control['mean_contribution'])} para {money(treatment['mean_contribution'])}.

O efeito estimado na metrica primaria foi **{money(experiment['difference'])} por cliente**, com IC 95% de [{money(low)}; {money(high)}], teste de Welch p = {experiment['welch_p_value']:.6g}. O intervalo bootstrap foi [{money(experiment['bootstrap_ci_95'][0])}; {money(experiment['bootstrap_ci_95'][1])}]. Sao {control['n']} clientes no controle e {treatment['n']} no tratamento; teste de balanceamento da alocacao (SRM) p = {experiment['srm_p_value']:.4f}.

## Contexto operacional

- Receita liquida anual: **{money(revenue)}**.
- Contribuicao apos CMV e custo de atendimento/logistica: **{money(contribution)}**, margem de **{contribution / revenue:.2%}**.
- Pedidos entregues: **{int(monthly.delivered_orders.sum())}**.
- Duplicatas identicas de pedidos removidas: **{audit['orders']['exact_duplicates_removed']}**.

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
"""
    (out / "executive_summary.md").write_text(summary, encoding="utf-8")
    tables = "".join(f'<section><h2>{html.escape(label)}</h2><div class="table">{frame.to_html(index=False, border=0, float_format=lambda v: f"{v:,.2f}")}</div></section>' for label, frame in [("Indicadores mensais", monthly), ("Categorias", category), ("Segmentos RFM", rfm_summary)])
    document = f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Retail Analytics Lab — relatorio</title>
<style>body{{margin:0;background:#0b1320;color:#dce8f4;font:16px/1.6 system-ui,sans-serif}}main{{max-width:1200px;margin:auto;padding:28px}}svg{{width:100%;height:auto}}section{{margin:24px 0;padding:24px;background:#111e30;border-radius:12px}}h1,h2{{line-height:1.2}}.tag{{color:#62d4c0}}.table{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:10px;text-align:right;border-bottom:1px solid #27364a}}th:first-child,td:first-child{{text-align:left}}button{{background:#62d4c0;border:0;border-radius:6px;padding:10px 16px;cursor:pointer}}.muted{{color:#9eafc1}}@media print{{body{{background:white;color:black}}section{{background:white}}button{{display:none}}}}</style>
<main><p class="tag">PORTFOLIO · DADOS SIMULADOS · ANO 2025</p><h1>Quando vender mais reduz o resultado</h1><p>Python, SQL e estatistica para avaliar um desconto pela contribuicao por cliente.</p>{svg}
<section><h2>{html.escape(experiment['decision'])}</h2><p>A conversao variou {experiment['conversion_difference_pp']:+.2f} p.p., enquanto a contribuicao por cliente variou {money(experiment['difference'])}. IC 95%: [{money(low)}; {money(high)}]. Todos os clientes sorteados entram na conta, inclusive quem nao comprou.</p><p class="muted">O efeito e programado na simulacao. O resultado nao descreve uma empresa real nem demonstra retorno comercial real.</p></section>
<button onclick="document.getElementById('details').hidden=!document.getElementById('details').hidden">Mostrar ou ocultar tabelas</button><div id="details">{tables}</div>
<section><h2>Como ler</h2><p>Receita liquida = vendas entregues apos descontos. Contribuicao = receita menos CMV e logistica. Margem bruta por categoria exclui logistica. Celulas cinza nas coortes representam janelas incompletas.</p><p>Serie historica observacional; experimento independente com alocacao 50/50 esperada. Horizonte fixo de 14 dias, uma metrica primaria, teste de Welch e bootstrap por cliente.</p><p class="muted">Nao inclui impostos, custos fixos, custo de aquisicao nem efeitos de longo prazo. Consulte docs/experiment_design.md e reports/executive_summary.md.</p></section></main></html>'''
    (out / "report.html").write_text(document, encoding="utf-8")
