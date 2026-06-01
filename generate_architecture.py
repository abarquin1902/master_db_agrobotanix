# python3 generate_architecture.py

import os, requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

RENDER_API_KEY = os.getenv("RENDER_API_KEY")

# ── Supabase clients
# supa_analytics   = create_client(os.getenv("SUPABASE_URL_ANALYTICS"),   os.getenv("SUPABASE_KEY_ANALYTICS"))
# supa_agentes     = create_client(os.getenv("SUPABASE_URL_AGENTES"),     os.getenv("SUPABASE_KEY_AGENTES"))
# supa_shopify     = create_client(os.getenv("SUPABASE_URL_SHOPIFY"),     os.getenv("SUPABASE_KEY_SHOPIFY"))
# supa_agrobotanix = create_client(os.getenv("SUPABASE_URL_AGROBOTANIX"), os.getenv("SUPABASE_KEY_AGROBOTANIX"))
supa_analytics   = create_client(os.getenv("SUPABASE_URL"),                    os.getenv("SUPABASE_KEY"))
supa_agentes     = create_client(os.getenv("SUPABASE_URL_AGENT_CONVERSATIONS"), os.getenv("SUPABASE_KEY_AGENT_CONVERSATIONS"))
supa_shopify     = create_client(os.getenv("SUPABASE_URL_MSTR_CTRL_SHOPIFY"),   os.getenv("SUPABASE_KEY_MSTR_CTRL_SHOPIFY"))
supa_agrobotanix = create_client(os.getenv("SUPABASE_URL_ZOHO_ASISTENCIAS"),    os.getenv("SUPABASE_KEY_ZOHO_ASISTENCIAS"))

def get_render_services():
    r = requests.get(
        "https://api.render.com/v1/services?limit=100",
        headers={"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json"}
    )
    return r.json()

def get_render_crons():
    r = requests.get(
        "https://api.render.com/v1/services?limit=100&type=cron_job",
        headers={"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json"}
    )
    items = r.json()
    result = {}
    for s in items:
        svc = s.get("service", {})
        name = svc.get("name")
        details = svc.get("serviceDetails", {})
        result[name] = {
            "schedule": details.get("schedule", ""),
            "last_run": details.get("lastSuccessfulRunAt", "")
        }
    return result

def count_tables(client, schema="public"):
    try:
        res = client.rpc("pg_catalog.pg_tables", {}).execute()
    except:
        pass
    try:
        res = client.from_("information_schema.tables")\
            .select("table_name,table_type")\
            .eq("table_schema", schema)\
            .execute()
        tables = [r for r in res.data if not r["table_name"].startswith("_")]
        base   = len([t for t in tables if t["table_type"] == "BASE TABLE"])
        views  = len([t for t in tables if t["table_type"] == "VIEW"])
        return base, views
    except:
        return 0, 0

def get_table_counts():
    counts = {}
    for name, client in [
        ("analytics",   supa_analytics),
        ("agentes",     supa_agentes),
        ("shopify",     supa_shopify),
        ("agrobotanix", supa_agrobotanix),
    ]:
        b, v = count_tables(client)
        counts[name] = {"tables": b, "views": v}
    return counts

def parse_cron_human(cron: str) -> str:
    mapping = {
        "0 13 * * *":    "7:00am CST · diario",
        "0 0 * * *":     "6:00pm CST · diario",
        "0 15 * * *":    "9:00am CST · diario",
        "0 7 * * *":     "1:00am CST · diario",
        "0 8 * * *":     "2:00am CST · diario",
        "30 1 * * *":    "7:30pm CST · diario",
        "*/30 * * * *":  "cada 30 min",
        "59 1 * * 1-5":  "7:59pm CST · lun–vie",
        "0 * * * *":     "cada hora",
        "*/5 * * * *":   "cada 5 min",
    }
    return mapping.get(cron.strip(), cron)

SERVICES_META = {
    "Cron ML Data": {
        "desc": "Actualiza datos de ML, Amazon y Meta Ads en Supabase",
        "category": "analytics", "repo": "marketplace-analytics"
    },
    "Cron Supermetrics": {
        "desc": "Jala datos de campañas Meta desde Google Sheets vía Supermetrics",
        "category": "analytics", "repo": "meta_supermetrics"
    },
    "nfg-metricas-agentes": {
        "desc": "Actualiza métricas de todos los agentes AI de NFG",
        "category": "analytics", "repo": "project_tracking"
    },
    "api_data_sustentabilidad": {
        "desc": "Registra el impacto de personas alcanzadas por TRG",
        "category": "analytics", "repo": "dashboard_sustentabilidad",
        "link": "https://abarquin1902.github.io/master_db_agrobotanix/trg_sustentabilidad.html"
    },
    "cron_sistema_virtual_recordatorios": {
        "desc": "Actualiza data de ventas y métricas del sistema de recordatorios",
        "category": "recordatorios", "repo": "cron_sistema_virtual_recordatorios",
        "link": "https://abarquin1902.github.io/master_db_agrobotanix/trg_optin_dashboardsrec.html"
    },
    "trg-notificaciones-cron": {
        "desc": "Ejecuta y despacha recordatorios de recompra vía WhatsApp",
        "category": "recordatorios", "repo": "the_real_green_agent"
    },
    "zoho_people_analytics": {
        "desc": "Consolida ventas de TRG, AGR y DREA desde Zoho People",
        "category": "recordatorios", "repo": "zoho_people_analytics"
    },
    "zoho_people_notifycliq": {
        "desc": "Envía notificaciones a empleados para recordarles hacer check-in",
        "category": "recordatorios", "repo": "zoho_people_analytics"
    },
    "zoho_people_force_checkout": {
        "desc": "Checkout automático a empleados que no registraron salida",
        "category": "recordatorios", "repo": "zoho_people_analytics"
    },
    "shopify_master_control": {
        "desc": "Recibe y procesa órdenes entrantes de Shopify en tiempo real",
        "category": "operaciones", "repo": "shopify_master_control"
    },
    "shopify_process_queue": {
        "desc": "Procesa la cola de órdenes pendientes y las mueve a órdenes finales",
        "category": "operaciones", "repo": "shopify_master_control"
    },
    "updating_trg_products": {
        "desc": "Actualiza el catálogo de productos TRG desde Shopify Admin API",
        "category": "operaciones", "repo": "nfg_qdrant_collections"
    },
    "external-checkin-nfg": {
        "desc": "App de check-in para personas sin cuenta Zoho",
        "category": "operaciones", "repo": "external-checkin-app",
        "link": "https://abarquin1902.github.io/master_db_agrobotanix/external-check-in-dashboard.html",
        "link2": "https://external-checkin-nfg.onrender.com/"
    },
    "the_real_green_agent": {
        "desc": "Agente AI de atención a clientes TRG vía WhatsApp",
        "category": "agentes", "repo": "the_real_green_agent"
    },
    "drea_agent": {
        "desc": "Agente AI de atención a clientes DREA vía WhatsApp",
        "category": "agentes", "repo": "drea_agent"
    },
    "Agente Agrobotanix": {
        "desc": "Agente AI de atención a clientes AGR vía WhatsApp",
        "category": "agentes", "repo": "agente_agrobotanix",
        "link": "https://agrobotanix.com/pages/dashboard-agrobotanix"
    },
    "ai_ds_activities": {
        "desc": "Tablero de actividades del área Data & AI para Dirección General",
        "category": "agentes", "repo": "ia_ds_activities",
        "link": "https://ai-ds-activities.onrender.com/"
    },
    "generador_anuncios_agrobotanix": {
        "desc": "Generador automático de anuncios de imágenes en bulk para Agrobotanix",
        "category": "agentes", "repo": "gen_anuncios_agro"
    },
    "project-manager-nfg": {
        "desc": "Project manager interno — gestión de tareas con alertas automáticas a 3 días y 1 día de vencimiento vía Zoho Cliq",
        "category": "operaciones",
        "repo": "project-manager-nfg",
        "link": "https://project-manager-nfg.onrender.com/dashboard"
    },
}

SUPABASE_PROJECTS = {
    "Marketplace Analytics": {
        "account": "alma.valdes@nfg.com.mx", "key": "analytics",
        "tables": ["sales","meta_advertising","ml_advertising","platform_tokens","sku_business_unit"],
        "views": ["v_pnl_resumen_bu","v_pnl_neto","v_resumen_bu","v_resumen_bu_amazon",
                  "v_resumen_bu_completo","v_resumen_mes","v_tendencia_diaria",
                  "v_tendencia_diaria_amazon","v_productos","v_publicidad_mes",
                  "v_comparativo_meses","v_tasa_recompra_ml","campaign_roi"]
    },
    "Agentes / Wati": {
        "account": "alma.valdes@nfg.com.mx", "key": "agentes",
        "tables": ["conversaciones","asignaciones_ejecutivo","notificaciones_programadas",
                   "compradores_agente","metricas_agentes","metricas_recordatorios",
                   "reporte_recompras","usuarios"],
        "views": ["v_recompra_kpis","v_recompra_por_mes","v_recompra_por_producto",
                  "v_recordatorios_por_mes","vista_recordatorios_pivot",
                  "vista_recordatorios_por_intento"]
    },
    "Shopify Master Control": {
        "account": "abarquin@nanobotanix.com", "key": "shopify",
        "tables": ["orders_raw","orders_processing_queue","orders_final",
                   "product_catalog","order_items"],
        "views": ["v_conversion_por_canal","v_productos_tendencia","v_productos_ventas",
                  "v_ranking_mensual","v_tasa_recompra","v_promedio_ventas_por_dia"]
    },
    "Master DB Agrobotanix": {
        "account": "abarquin@nanobotanix.com", "key": "agrobotanix",
        "tables": ["raw_meta_ads_daily","asistencia_diaria","kiosk_attendance",
                   "kiosk_employees","empleados","ubicaciones",
                   "producto_catalogo","trg_sustentabilidad_snapshot"],
        "views": ["v_ad_efficiency","v_campaign_monthly","v_daily_spend",
                  "v_investment_comparison","v_top_performers","v_alertas_marketing"]
    },
    "Project Manager NFG": {
        "account": "abarquin@nanobotanix.com", "key": "agrobotanix",
        "tables": ["project_manager.users", "project_manager.tasks", "project_manager.notifications_log"],
        "views": []
    },
}

CATEGORIES = {
    "analytics":     {"label": "Analytics & Data",       "color": "blue"},
    "recordatorios": {"label": "Recordatorios & CRM",    "color": "coral"},
    "operaciones":   {"label": "Operaciones",            "color": "green"},
    "agentes":       {"label": "Agentes AI & Herramientas", "color": "purple"},
}

def build_html(services_raw, crons, table_counts):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Enrich services
    enriched = {}
    for s in services_raw:
        svc = s.get("service", {})
        name = svc.get("name", "")
        meta = SERVICES_META.get(name, {})
        cron_data = crons.get(name, {})
        enriched[name] = {
            "name": name,
            "type": svc.get("type", "web_service"),
            "repo": svc.get("repo", ""),
            "status": svc.get("suspended", "not_suspended"),
            "desc": meta.get("desc", ""),
            "category": meta.get("category", "operaciones"),
            "schedule": parse_cron_human(cron_data.get("schedule", "")),
            "link": meta.get("link", ""),
            "link2": meta.get("link2", ""),
        }

    def card(svc):
        name = svc["name"]
        repo_name = svc["repo"].split("/")[-1] if svc["repo"] else ""
        badge = "web" if svc["type"] == "web_service" else "cron"
        badge_label = "web" if badge == "web" else "cron"
        schedule_html = f'<span>⏰ {svc["schedule"]}</span>' if svc["schedule"] else '<span>⏰ siempre activo</span>'
        link_html = f'<a class="card-link" href="{svc["link"]}" target="_blank">↗ Ver tablero</a>' if svc["link"] else ""
        link2_html = f'<a class="card-link" href="{svc["link2"]}" target="_blank">↗ App</a>' if svc["link2"] else ""
        cat = svc["category"]
        return f'''
        <div class="card cat-{cat}">
          <div class="card-header">
            <span class="card-name">{name}</span>
            <span class="badge badge-{badge}">{badge_label}</span>
          </div>
          <div class="card-desc">{svc["desc"]}</div>
          <div class="card-meta">
            {schedule_html}
            <span>📦 {repo_name}</span>
          </div>
          {link_html}{link2_html}
        </div>'''

    def section(cat_key):
        cat = CATEGORIES[cat_key]
        cards = [card(s) for s in enriched.values() if s["category"] == cat_key]
        if not cards:
            return ""
        return f'''
    <div class="section">
      <div class="section-title">{cat["label"]}</div>
      <div class="cards">{"".join(cards)}</div>
    </div>
    <div class="divider"></div>'''

    def db_project(proj_name, proj):
        tables_html = "".join(f'<span class="tbl tbl-data">{t}</span>' for t in proj["tables"])
        views_html  = "".join(f'<span class="tbl tbl-view">{v}</span>' for v in proj["views"])
        key = proj["key"]
        tc = table_counts.get(key, {})
        live = f' <span class="live-count">({tc.get("tables",0)} tablas · {tc.get("views",0)} vistas en vivo)</span>' if tc else ""
        return f'''
      <div class="db-proj">
        <div class="db-proj-name">{proj_name}{live}</div>
        <div class="db-tables">{tables_html}{views_html}</div>
      </div>'''

    total_tables = sum(len(p["tables"]) + len(p["views"]) for p in SUPABASE_PROJECTS.values())
    total_svcs   = len(enriched)

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Arquitectura NFG</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f9f9f7;color:#2c2c2a;padding:24px 20px;max-width:1100px;margin:0 auto;}}
h1{{font-size:20px;font-weight:500;margin-bottom:4px;}}
.subtitle{{font-size:12px;color:#888;margin-bottom:20px;}}
.section{{margin-bottom:20px;}}
.section-title{{font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:#888;margin-bottom:10px;}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px;}}
.card{{border-radius:10px;padding:10px 12px;border:1px solid;}}
.card-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;}}
.card-name{{font-size:12px;font-weight:600;}}
.badge{{font-size:9px;font-weight:600;padding:2px 6px;border-radius:4px;}}
.badge-web{{background:#dbeafe;color:#1e40af;}}
.badge-cron{{background:#dcfce7;color:#166534;}}
.card-desc{{font-size:11px;color:#666;margin-bottom:5px;line-height:1.45;}}
.card-meta{{font-size:10px;color:#999;display:flex;flex-direction:column;gap:2px;}}
.card-link{{display:inline-flex;align-items:center;gap:3px;font-size:10px;font-weight:600;text-decoration:none;margin-top:5px;margin-right:4px;padding:2px 8px;border-radius:4px;background:#fef3c7;color:#92400e;border:1px solid #f59e0b;}}
.card-link:hover{{opacity:.8;}}
.cat-analytics{{background:#eff6ff44;border-color:#93c5fd;}}
.cat-recordatorios{{background:#fff7ed44;border-color:#fdba74;}}
.cat-operaciones{{background:#f0fdf444;border-color:#86efac;}}
.cat-agentes{{background:#faf5ff44;border-color:#c4b5fd;}}
.divider{{height:1px;background:#e5e4e0;margin:16px 0;}}
.flow{{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;}}
.flow-node{{font-size:11px;padding:4px 10px;border-radius:6px;background:#fff;border:1px solid #ddd;color:#444;}}
.flow-arrow{{font-size:14px;color:#aaa;}}
.db-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;}}
.db-block{{border-radius:10px;padding:12px;border:1px solid #e0dfd8;background:#fff;}}
.db-account{{font-size:10px;color:#aaa;margin-bottom:8px;}}
.db-proj{{margin-bottom:10px;}}
.db-proj-name{{font-size:12px;font-weight:600;margin-bottom:5px;color:#333;}}
.db-tables{{display:flex;flex-wrap:wrap;gap:4px;}}
.tbl{{font-size:10px;padding:2px 7px;border-radius:4px;}}
.tbl-data{{background:#dbeafe;color:#1e40af;}}
.tbl-view{{background:#f3f4f6;color:#374151;}}
.live-count{{font-size:10px;font-weight:400;color:#aaa;}}
.consumer-row{{display:flex;gap:8px;flex-wrap:wrap;}}
.consumer{{font-size:11px;padding:6px 12px;border-radius:8px;background:#fef3c7;border:1px solid #f59e0b;color:#92400e;font-weight:500;display:flex;flex-direction:column;gap:4px;}}
.consumer a{{font-size:10px;color:#b45309;text-decoration:none;font-weight:600;}}
.footer{{margin-top:16px;font-size:10px;color:#bbb;text-align:right;}}
@media(max-width:600px){{.db-grid{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<h1>Arquitectura de sistemas — Nanofactor Global</h1>
<div class="subtitle">Generado automáticamente · {now} · {total_svcs} servicios Render · {total_tables} tablas/vistas Supabase · todos activos</div>

<div class="section">
  <div class="section-title">Flujo de datos</div>
  <div class="flow">
    <div class="flow-node">Shopify · ML · Amazon · Meta</div>
    <div class="flow-arrow">→</div>
    <div class="flow-node">ETL en Render (crons)</div>
    <div class="flow-arrow">→</div>
    <div class="flow-node">Supabase (4 proyectos)</div>
    <div class="flow-arrow">→</div>
    <div class="flow-node">Zoho Analytics + Dashboards</div>
    <div class="flow-arrow">→</div>
    <div class="flow-node">CEO · Dirección · Clientes</div>
  </div>
</div>
<div class="divider"></div>

{"".join(section(k) for k in CATEGORIES)}

<div class="section">
  <div class="section-title">Supabase — bases de datos (2 cuentas · 4 proyectos)</div>
  <div class="db-grid">
    <div class="db-block">
      <div class="db-account">alma.valdes@nfg.com.mx</div>
      {"".join(db_project(n,p) for n,p in SUPABASE_PROJECTS.items() if p["account"]=="alma.valdes@nfg.com.mx")}
    </div>
    <div class="db-block">
      <div class="db-account">abarquin@nanobotanix.com</div>
      {"".join(db_project(n,p) for n,p in SUPABASE_PROJECTS.items() if p["account"]=="abarquin@nanobotanix.com")}
    </div>
  </div>
</div>
<div class="divider"></div>

<div class="section">
  <div class="section-title">Dashboards & salidas de negocio</div>
  <div class="consumer-row">
    <div class="consumer">Zoho Analytics<a href="https://analytics.zoho.com" target="_blank">↗ Abrir</a></div>
    <div class="consumer">Tablero Sustentabilidad<a href="https://abarquin1902.github.io/master_db_agrobotanix/trg_sustentabilidad.html" target="_blank">↗ Ver</a></div>
    <div class="consumer">Tablero Recordatorios<a href="https://abarquin1902.github.io/master_db_agrobotanix/trg_optin_dashboardsrec.html" target="_blank">↗ Ver</a></div>
    <div class="consumer">Tablero Actividades DS<a href="https://ai-ds-activities.onrender.com/" target="_blank">↗ Ver</a></div>
    <div class="consumer">External Check-in<a href="https://abarquin1902.github.io/master_db_agrobotanix/external-check-in-dashboard.html" target="_blank">↗ Tablero</a><a href="https://external-checkin-nfg.onrender.com/" target="_blank">↗ App</a></div>
    <div class="consumer">Mapa Agrobotanix<a href="https://agrobotanix.com/pages/dashboard-agrobotanix" target="_blank">↗ Ver</a></div>
  </div>
</div>

<div class="footer">Generado por generate_architecture.py · {now}</div>
</body>
</html>'''

    return html

def run():
    print("🏗  Generando architecture.html...")
    print("  → Jalando servicios de Render...")
    services = get_render_services()
    crons    = get_render_crons()

    print("  → Contando tablas en Supabase...")
    table_counts = get_table_counts()

    print("  → Generando HTML...")
    html = build_html(services, crons, table_counts)

    output_path = "architecture.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ architecture.html generado en {os.path.abspath(output_path)}")

if __name__ == "__main__":
    run()