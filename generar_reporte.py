# python3 generar_reporte.py

"""
Lee datos_maestros.csv y genera reporte_nanofactor.html con datos reales.
"""

import pandas as pd

# ── Cargar datos ──────────────────────────────────────────────────────────────
df = pd.read_csv("datos_maestros.csv")

MES_ORDER = ["Febrero 2026", "Marzo 2026", "Abril 2026", "Mayo 2026"]
BU_ORDER  = ["TRG", "Agrobotanix", "DREA"]

def mes_idx(m): return MES_ORDER.index(m) if m in MES_ORDER else 99
def bu_idx(b):  return BU_ORDER.index(b)  if b in BU_ORDER  else 99

# ── Aggregaciones ─────────────────────────────────────────────────────────────
total_usuarios    = int(df["usuarios"].sum())
total_compradores = int(df["compradores"].sum())
total_revenue     = float(df["revenue"].sum())
total_ordenes     = int(df["ordenes"].sum())
tasa_global       = round(total_compradores / total_usuarios * 100, 1) if total_usuarios else 0
hrs_ahorradas     = round(total_usuarios * 3 / 60, 1)
dias_laborales    = round(hrs_ahorradas / 8, 1)
ahorro_estimado   = round(dias_laborales * 350, 2)

# Por BU global
by_bu = df.groupby("business_unit").agg(
    usuarios=("usuarios","sum"), compradores=("compradores","sum"),
    ordenes=("ordenes","sum"), revenue=("revenue","sum"),
).reset_index()
by_bu["tasa"]   = (by_bu["compradores"] / by_bu["usuarios"] * 100).round(1)
by_bu["ticket"] = (by_bu["revenue"] / by_bu["ordenes"].replace(0, float("nan"))).round(2).fillna(0)
by_bu["_order"] = by_bu["business_unit"].apply(bu_idx)
by_bu = by_bu.sort_values("_order")

# Por BU + mes
by_bu_mes = df.groupby(["business_unit","mes"]).agg(
    usuarios=("usuarios","sum"), compradores=("compradores","sum"),
    ordenes=("ordenes","sum"), revenue=("revenue","sum"),
).reset_index()
by_bu_mes["tasa"]    = (by_bu_mes["compradores"] / by_bu_mes["usuarios"] * 100).round(1)
by_bu_mes["_bu_ord"] = by_bu_mes["business_unit"].apply(bu_idx)
by_bu_mes["_m_ord"]  = by_bu_mes["mes"].apply(mes_idx)
by_bu_mes = by_bu_mes.sort_values(["_bu_ord","_m_ord"])

# Por mes global
by_mes = df.groupby("mes").agg(
    usuarios=("usuarios","sum"), compradores=("compradores","sum"), revenue=("revenue","sum"),
).reset_index()
by_mes["hrs"] = (by_mes["usuarios"] * 3 / 60).round(1)
by_mes["_order"] = by_mes["mes"].apply(mes_idx)
by_mes = by_mes.sort_values("_order")

# ── Helpers ───────────────────────────────────────────────────────────────────
BADGE = {
    "TRG":         '<span class="badge badge-trg">TRG</span>',
    "Agrobotanix": '<span class="badge badge-agro">Agrobotanix</span>',
    "DREA":        '<span class="badge badge-drea">DREA</span>',
    "TOTAL":       '<span class="badge badge-total">TOTAL</span>',
}

def pct_bar(pct, max_pct=20.0):
    w = min(pct / max_pct * 100, 100)
    return f'<div class="pct-bar-wrap"><div class="pct-bar"><div class="pct-bar-fill" style="width:{w:.1f}%"></div></div><span class="pct-text">{pct:.1f}%</span></div>'

def fn(v): return f"{int(v):,}"
def fr(v): return f"${float(v):,.2f}"

# ── Tabla conversión por BU con desglose mensual ──────────────────────────────
rows_conv = ""
for bu in BU_ORDER:
    bu_data = by_bu[by_bu["business_unit"] == bu]
    if bu_data.empty: continue
    r = bu_data.iloc[0]
    color = 'style="color:var(--green-500);font-weight:700;"' if r["tasa"] > 0 else ""
    tasa_td = f'<td class="num" {color}>{r["tasa"]:.1f}%</td>' if r["tasa"] > 0 else '<td class="num">—</td>'
    rows_conv += f"""
        <tr class="bu-row">
          <td>{BADGE.get(bu, bu)}</td>
          <td class="num"><strong>{fn(r['usuarios'])}</strong></td>
          <td class="num"><strong>{fn(r['compradores'])}</strong></td>
          <td class="num">{pct_bar(r['tasa'])}</td>
          {tasa_td}
        </tr>"""
    # desglose por mes
    meses_bu = by_bu_mes[by_bu_mes["business_unit"] == bu]
    for _, mr in meses_bu.iterrows():
        t_td = f'<td class="num sub-val">{mr["tasa"]:.1f}%</td>' if mr["tasa"] > 0 else '<td class="num sub-val">—</td>'
        rows_conv += f"""
        <tr class="mes-row">
          <td class="sub-label">↳ {mr['mes']}</td>
          <td class="num sub-val">{fn(mr['usuarios'])}</td>
          <td class="num sub-val">{fn(mr['compradores'])}</td>
          <td class="num sub-val">{pct_bar(mr['tasa'])}</td>
          {t_td}
        </tr>"""

rows_conv += f"""
        <tr class="total-row">
          <td>{BADGE['TOTAL']}</td>
          <td class="num">{fn(total_usuarios)}</td>
          <td class="num">{fn(total_compradores)}</td>
          <td class="num">—</td>
          <td class="num" style="color:var(--green-600);font-weight:800;">{tasa_global:.1f}%</td>
        </tr>"""

# ── Tabla revenue por BU con desglose mensual ─────────────────────────────────
rows_rev = ""
for bu in BU_ORDER:
    bu_data = by_bu[by_bu["business_unit"] == bu]
    if bu_data.empty: continue
    r = bu_data.iloc[0]
    ticket_str = fr(r["ticket"]) if r["ordenes"] > 0 else "—"
    rev_color = 'style="color:var(--green-600);font-weight:700;"' if r["revenue"] > 0 else ""
    rows_rev += f"""
        <tr class="bu-row">
          <td>{BADGE.get(bu, bu)}</td>
          <td class="num"><strong>{fn(r['ordenes'])}</strong></td>
          <td class="num" {rev_color}><strong>{fr(r['revenue'])}</strong></td>
          <td class="num">{ticket_str}</td>
        </tr>"""
    meses_bu = by_bu_mes[by_bu_mes["business_unit"] == bu]
    for _, mr in meses_bu.iterrows():
        rev_sub = fr(mr["revenue"]) if mr["revenue"] > 0 else "$0.00"
        tk_sub  = fr(mr["revenue"] / mr["ordenes"]) if mr["ordenes"] > 0 else "—"
        rows_rev += f"""
        <tr class="mes-row">
          <td class="sub-label">↳ {mr['mes']}</td>
          <td class="num sub-val">{fn(mr['ordenes'])}</td>
          <td class="num sub-val">{rev_sub}</td>
          <td class="num sub-val">{tk_sub}</td>
        </tr>"""

rows_rev += f"""
        <tr class="total-row">
          <td>{BADGE['TOTAL']}</td>
          <td class="num">{fn(total_ordenes)}</td>
          <td class="num" style="color:var(--green-600);font-weight:800;">{fr(total_revenue)}</td>
          <td class="num">{fr(total_revenue/total_ordenes) if total_ordenes else '—'}</td>
        </tr>"""

# ── Cards desglose mensual por BU ─────────────────────────────────────────────
cards_mes = ""
for mes in MES_ORDER:
    mes_data = by_bu_mes[by_bu_mes["mes"] == mes]
    if mes_data.empty: continue
    mes_total_rev = mes_data["revenue"].sum()
    mes_total_usr = mes_data["usuarios"].sum()
    mes_total_comp= mes_data["compradores"].sum()
    cards_mes += f"""
    <div class="month-card">
      <div class="month-name">{mes}</div>
"""
    for _, r in mes_data.sort_values("_bu_ord").iterrows():
        rev_str  = fr(r["revenue"]) if r["revenue"] > 0 else "$0.00"
        comp_str = f'{fn(r["compradores"])} compraron' if r["compradores"] > 0 else "0 compraron"
        comp_color = "color:var(--green-500);font-weight:600;" if r["compradores"] > 0 else "color:var(--ink-muted);"
        cards_mes += f"""
      <div class="month-bu-row">
        <span class="month-bu-badge">{BADGE.get(r['business_unit'], r['business_unit'])}</span>
        <div class="month-bu-stats">
          <span>{fn(r['usuarios'])} usu. · <span style="{comp_color}">{comp_str}</span></span>
          <span class="rev-small">{rev_str}</span>
        </div>
      </div>"""
    cards_mes += f"""
      <div class="month-revenue">Ventas generadas: {fr(mes_total_rev)}</div>
    </div>"""

# ── HTML ──────────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nanofactor — Reporte Agentes IA</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --green-50:#f0faf4;--green-100:#d6f2e0;--green-200:#a8e0bc;--green-400:#4caf78;
    --green-500:#2e9156;--green-600:#1e7040;--green-700:#155230;
    --ink:#0f1f16;--ink-light:#3a5445;--ink-muted:#6b8c7a;
    --surface:#f7fbf8;--surface-2:#edf7f1;--border:#cde8d6;--white:#ffffff;
  }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Inter',sans-serif;background:var(--surface);color:var(--ink);min-height:100vh}}

  .header{{background:var(--white);border-bottom:1.5px solid var(--border);padding:36px 64px 28px;display:flex;justify-content:space-between;align-items:flex-end}}
  .header-left h1{{font-size:11px;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:var(--green-500);margin-bottom:6px}}
  .header-left h2{{font-size:28px;font-weight:800;color:var(--ink);line-height:1.15}}
  .header-right .periodo{{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--ink-muted);text-align:right;line-height:1.8}}
  .header-right .periodo span{{color:var(--green-500);font-weight:500}}

  .main{{max-width:1160px;margin:0 auto;padding:48px 40px 80px}}

  .section-title{{font-size:10.5px;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-muted);margin-bottom:20px;display:flex;align-items:center;gap:10px}}
  .section-title::after{{content:'';flex:1;height:1px;background:var(--border)}}

  .kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:48px}}
  .kpi-card{{background:var(--white);border:1.5px solid var(--border);border-radius:12px;padding:24px 22px 20px;position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s;animation:fadeUp .5s ease both}}
  .kpi-card:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(46,145,86,.08)}}
  .kpi-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--green-400);border-radius:12px 12px 0 0}}
  .kpi-card.highlight{{background:var(--green-700);border-color:var(--green-600)}}
  .kpi-card.highlight::before{{background:var(--green-200)}}
  .kpi-label{{font-size:10.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-muted);margin-bottom:10px}}
  .kpi-card.highlight .kpi-label{{color:rgba(166,224,188,.8)}}
  .kpi-value{{font-size:32px;font-weight:800;color:var(--ink);line-height:1;margin-bottom:5px}}
  .kpi-card.highlight .kpi-value{{color:var(--white)}}
  .kpi-sub{{font-family:'JetBrains Mono',monospace;font-size:10.5px;color:var(--ink-muted)}}
  .kpi-card.highlight .kpi-sub{{color:rgba(166,224,188,.7)}}
  .kpi-card:nth-child(1){{animation-delay:.05s}}.kpi-card:nth-child(2){{animation-delay:.10s}}.kpi-card:nth-child(3){{animation-delay:.15s}}.kpi-card:nth-child(4){{animation-delay:.20s}}

  .tiempo-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:48px}}
  .tiempo-card{{background:var(--white);border:1.5px solid var(--border);border-radius:12px;padding:22px 20px;animation:fadeUp .5s ease both;animation-delay:.25s}}
  .tiempo-card-title{{font-size:10.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-muted);margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--border)}}
  .tiempo-big{{font-size:36px;font-weight:800;color:var(--green-600);line-height:1;margin-bottom:4px}}
  .tiempo-label{{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--ink-muted);margin-bottom:14px}}
  .tiempo-desglose{{display:flex;flex-direction:column;gap:6px}}
  .tiempo-row{{display:flex;justify-content:space-between;font-size:12px;color:var(--ink-light)}}
  .tiempo-row span:last-child{{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--green-500);font-weight:500}}

  .table-wrap{{background:var(--white);border:1.5px solid var(--border);border-radius:14px;overflow:hidden;margin-bottom:40px;animation:fadeUp .5s ease both;animation-delay:.3s}}
  table{{width:100%;border-collapse:collapse}}
  thead tr{{background:var(--surface-2);border-bottom:1.5px solid var(--border)}}
  thead th{{font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-muted);padding:13px 20px;text-align:left}}
  thead th.num{{text-align:right}}
  tbody tr{{border-bottom:1px solid var(--border);transition:background .15s}}
  tbody tr:last-child{{border-bottom:none}}
  tbody tr:hover{{background:var(--green-50)}}
  tbody tr.total-row{{background:var(--surface-2);border-top:1.5px solid var(--border);font-weight:700}}
  tbody tr.total-row:hover{{background:var(--green-100)}}
  tbody tr.bu-row{{background:var(--surface-2)}}
  tbody tr.mes-row td{{padding:8px 20px 8px 32px;font-size:12px;color:var(--ink-muted)}}
  tbody tr.mes-row:hover{{background:var(--green-50)}}
  .sub-label{{font-size:12px;color:var(--ink-muted)}}
  .sub-val{{font-size:11.5px;color:var(--ink-muted)}}
  td{{padding:13px 20px;font-size:13.5px;color:var(--ink)}}
  td.num{{text-align:right;font-family:'JetBrains Mono',monospace;font-size:12.5px}}

  .badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:10.5px;font-weight:600}}
  .badge-trg{{background:#dff2e8;color:#1e7040}}
  .badge-agro{{background:#d6edf8;color:#1a5f8a}}
  .badge-drea{{background:#f0e8ff;color:#5a2d9a}}
  .badge-total{{background:var(--green-700);color:var(--white)}}

  .pct-bar-wrap{{display:flex;align-items:center;gap:10px;justify-content:flex-end}}
  .pct-bar{{width:70px;height:5px;background:var(--border);border-radius:3px;overflow:hidden}}
  .pct-bar-fill{{height:100%;background:var(--green-400);border-radius:3px}}
  .pct-text{{font-family:'JetBrains Mono',monospace;font-size:12px;min-width:38px;text-align:right}}

  .month-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:48px}}
  .month-card{{background:var(--white);border:1.5px solid var(--border);border-radius:12px;padding:20px 18px;transition:transform .2s,box-shadow .2s;animation:fadeUp .5s ease both;animation-delay:.35s}}
  .month-card:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(46,145,86,.08)}}
  .month-name{{font-size:10.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-muted);margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid var(--border)}}
  .month-total-row{{display:flex;justify-content:space-between;font-size:11.5px;color:var(--ink);margin-bottom:10px;padding-bottom:8px;border-bottom:1px dashed var(--border)}}
  .month-comp{{color:var(--green-500);font-weight:600}}
  .month-bu-row{{display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;gap:6px}}
  .month-bu-badge{{flex-shrink:0}}
  .month-bu-stats{{display:flex;flex-direction:column;align-items:flex-end;gap:1px}}
  .month-bu-stats span{{font-family:'JetBrains Mono',monospace;font-size:10.5px;color:var(--ink-muted)}}
  .rev-small{{color:var(--green-600)!important;font-weight:500!important}}
  .month-revenue{{margin-top:10px;padding-top:10px;border-top:1px solid var(--border);font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;color:var(--green-600);text-align:right}}

  .note{{background:#fffbeb;border:1px solid #f0d060;border-radius:8px;padding:14px 18px;font-size:12px;color:#7a5f10;margin-bottom:40px;line-height:1.7}}
  .note strong{{color:#5a4200}}

  @keyframes fadeUp{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:translateY(0)}}}}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <h1>Nanofactor Global</h1>
    <h2>Reporte de Agentes IA</h2>
  </div>
  <div class="header-right">
    <div class="periodo">Periodo analizado<br><span>Febrero — Mayo 2026</span></div>
  </div>
</div>

<div class="main">

  <div class="section-title">Resumen General</div>
  <div class="kpi-grid">
    <div class="kpi-card highlight">
      <div class="kpi-label">Usuarios Atendidos</div>
      <div class="kpi-value">{fn(total_usuarios)}</div>
      <div class="kpi-sub">Total Nanofactor Global</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Compradores</div>
      <div class="kpi-value">{fn(total_compradores)}</div>
      <div class="kpi-sub">usuarios que convirtieron</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Tasa de Conversión</div>
      <div class="kpi-value">{tasa_global:.1f}%</div>
      <div class="kpi-sub">promedio global</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Ventas Generadas</div>
      <div class="kpi-value">${total_revenue/1000:.1f}k</div>
      <div class="kpi-sub">MXN confirmado</div>
    </div>
  </div>

  <div class="section-title">Tiempo Ahorrado — 3 min promedio por conversación</div>
  <div class="tiempo-grid">
    <div class="tiempo-card">
      <div class="tiempo-card-title">Total Horas Ahorradas</div>
      <div class="tiempo-big">{hrs_ahorradas} h</div>
      <div class="tiempo-label">{fn(total_usuarios)} usuarios × 3 min</div>
      <div class="tiempo-desglose">
        {"".join(f'<div class="tiempo-row"><span>{r["mes"]}</span><span>{r["hrs"]} h</span></div>' for _, r in by_mes.iterrows())}
      </div>
    </div>
    <div class="tiempo-card">
      <div class="tiempo-card-title">Equivalente en Días Laborales</div>
      <div class="tiempo-big">{dias_laborales}</div>
      <div class="tiempo-label">días de 8 horas de trabajo</div>
      <div class="tiempo-desglose">
        <div class="tiempo-row"><span>Costo est. agente humano</span><span>$350/día</span></div>
        <div class="tiempo-row"><span>Ahorro estimado</span><span>${ahorro_estimado:,.0f} MXN</span></div>
        <div class="tiempo-row"><span>Disponibilidad agente IA</span><span>24/7</span></div>
        <div class="tiempo-row"><span>Resp. promedio humano</span><span>&gt;2 hrs</span></div>
        <div class="tiempo-row"><span>Resp. agente IA</span><span>&lt;30 seg</span></div>
      </div>
    </div>
    <div class="tiempo-card">
      <div class="tiempo-card-title">Usuarios por Mes</div>
      <div class="tiempo-big">{fn(int(by_mes['usuarios'].mean()))}</div>
      <div class="tiempo-label">promedio mensual atendidos</div>
      <div class="tiempo-desglose">
        {"".join(f'<div class="tiempo-row"><span>{r["mes"]}</span><span>{fn(int(r["usuarios"]))} usuarios</span></div>' for _, r in by_mes.iterrows())}
      </div>
    </div>
  </div>

  <div class="section-title">Conversión por Unidad de Negocio</div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Unidad / Mes</th>
          <th class="num">Usuarios</th>
          <th class="num">Compraron</th>
          <th class="num">% Conversión</th>
          <th class="num">Tasa</th>
        </tr>
      </thead>
      <tbody>{rows_conv}</tbody>
    </table>
  </div>

  <div class="note">
    <strong>Nota sobre Agrobotanix (feb–mar):</strong> Las ventas de este periodo se realizaron principalmente vía Mercado Libre, cuyas transacciones se registran en el sistema TRG. El análisis de conversión contra Shopify propio subestima significativamente el impacto real del agente en este periodo.
  </div>

  <div class="section-title">Ventas Generadas por Unidad de Negocio (MXN)</div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Unidad / Mes</th>
          <th class="num">Órdenes</th>
          <th class="num">Ventas Generadas</th>
          <th class="num">Ticket Promedio</th>
        </tr>
      </thead>
      <tbody>{rows_rev}</tbody>
    </table>
  </div>

  <div class="section-title">Desglose Mensual por Unidad de Negocio</div>
  <div class="month-grid">{cards_mes}</div>

</div>
</body>
</html>"""

with open("reporte_nanofactor.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ reporte_nanofactor.html generado")
print(f"   {total_usuarios:,} usuarios | {total_compradores} compradores | ${total_revenue:,.2f} MXN")