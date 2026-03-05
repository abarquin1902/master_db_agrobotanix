# python3 generar_mapa_agrobotanix.py

"""
Agrobotanix — Generador de Mapa Interactivo (ESTE SCRIPT SOLO GENERA EL MAPA INTERACTIVO, NO LAS TRES PESTAÑAS QUE CONTIENE EL 
REPORTE COMPLETO)
Genera un HTML autónomo con Leaflet + circleMarker por estado.
Uso: python generar_mapa_agrobotanix.py
"""

import json
import pandas as pd
from collections import defaultdict

# ─── Rutas ────────────────────────────────────────────────────────────────────
EXCEL_PATH  = "master_db_agrobotanix.xlsx"
OUTPUT_HTML = "mapa_agrobotanix.html"

# ─── Coordenadas capitales estatales ─────────────────────────────────────────
COORDENADAS = {
    "aguascalientes":      {"lat": 21.8853, "lon": -102.2916},
    "baja california":     {"lat": 32.6245, "lon": -115.4523},
    "baja california sur": {"lat": 24.1426, "lon": -110.3128},
    "campeche":            {"lat": 19.8301, "lon": -90.5349},
    "chiapas":             {"lat": 16.7569, "lon": -93.1292},
    "chihuahua":           {"lat": 28.6353, "lon": -106.0889},
    "coahuila":            {"lat": 25.4232, "lon": -101.0053},
    "colima":              {"lat": 19.2452, "lon": -103.7241},
    "durango":             {"lat": 24.0277, "lon": -104.6532},
    "edomex":              {"lat": 19.2827, "lon": -99.6557},
    "guanajuato":          {"lat": 21.0190, "lon": -101.2574},
    "guerrero":            {"lat": 17.5506, "lon": -99.5024},
    "hidalgo":             {"lat": 20.0911, "lon": -98.7624},
    "jalisco":             {"lat": 20.6597, "lon": -103.3496},
    "michoacan":           {"lat": 19.7060, "lon": -101.1950},
    "morelos":             {"lat": 18.9211, "lon": -99.2342},
    "nayarit":             {"lat": 21.5010, "lon": -104.8945},
    "nuevo leon":          {"lat": 25.6866, "lon": -100.3161},
    "oaxaca":              {"lat": 17.0732, "lon": -96.7266},
    "puebla":              {"lat": 19.0414, "lon": -98.2063},
    "queretaro":           {"lat": 20.5888, "lon": -100.3899},
    "quintana roo":        {"lat": 21.1619, "lon": -86.8515},
    "san luis potosi":     {"lat": 22.1565, "lon": -100.9855},
    "sinaloa":             {"lat": 24.8091, "lon": -107.3940},
    "sonora":              {"lat": 29.0729, "lon": -110.9559},
    "tabasco":             {"lat": 17.8409, "lon": -92.6189},
    "tamaulipas":          {"lat": 23.7369, "lon": -99.1411},
    "tlaxcala":            {"lat": 19.3139, "lon": -98.2404},
    "veracruz":            {"lat": 19.1738, "lon": -96.1342},
    "yucatan":             {"lat": 20.9674, "lon": -89.5926},
    "zacatecas":           {"lat": 22.7709, "lon": -102.5832},
}

# ─── Colores por cultivo ──────────────────────────────────────────────────────
COLORES_CULTIVO = {
    "aguacate":     "#2d6a4f",
    "cafe":         "#6b4226",
    "citricos (Naranja, Mandarina, Limon)": "#f4a11b",
    "hortaliza (chile, pepino, jitomate, tomate)": "#e74c3c",
    "mango":        "#e67e22",
    "platano":      "#f1c40f",
    "vid":          "#8e44ad",
    "fresa":        "#e91e8c",
    "frambuesa":    "#c0392b",
    "arandano":     "#2980b9",
    "zarzamora":    "#34495e",
    "papaya":       "#ff6b6b",
    "sandia":       "#27ae60",
    "calabaza":     "#d35400",
    "guanabana":    "#1abc9c",
    "pimienta":     "#7f8c8d",
    "durazno":      "#e59866",
    "nogal":        "#784212",
}


# ─── Carga y procesamiento ────────────────────────────────────────────────────
def cargar_datos():
    xl = pd.read_excel(EXCEL_PATH, sheet_name=None)
    enfermedades = xl["tbl_enfermedades"]
    calendario   = xl["tbl_cultivo_calendario"]
    exportacion  = xl["tbl_cultivo_exportacion"][["cultivo", "pct_exportacion"]].dropna()
    return enfermedades, calendario, exportacion


def construir_datos_estados(calendario, enfermedades, exportacion):
    exp_map = dict(zip(exportacion["cultivo"], exportacion["pct_exportacion"]))

    estado_cultivos = defaultdict(list)
    for _, row in calendario.iterrows():
        estado  = str(row["estado"]).lower().strip()
        cultivo = str(row["cultivo"]).strip()
        if cultivo not in estado_cultivos[estado]:
            estado_cultivos[estado].append(cultivo)

    enf_por_cultivo = defaultdict(list)
    for _, row in enfermedades.iterrows():
        enf_por_cultivo[row["cultivo"]].append({
            "nombre":     str(row["nombre_comun"]),
            "tipo":       str(row["tipo_patogeno"]),
            "dificultad": str(row["dificultad_erradicacion"]),
            "preventivo": str(row["producto_preventivo"]),
            "dosis_prev": str(row["dosis_preventivo"]),
            "correctivo": str(row["producto_correctivo"]),
            "dosis_corr": str(row["dosis_correctivo"]),
        })

    estados = []
    for estado, cultivos in estado_cultivos.items():
        coords = COORDENADAS.get(estado)
        if not coords:
            continue

        cultivos_detalle = []
        for c in cultivos:
            pct_exp   = exp_map.get(c, 0)
            enfs      = enf_por_cultivo.get(c, [])
            enfs_unicas = list({e["nombre"]: e for e in enfs}.values())
            cultivos_detalle.append({
                "nombre":       c,
                "color":        COLORES_CULTIVO.get(c, "#95a5a6"),
                "exportacion":  round(float(pct_exp) * 100, 1),
                "n_enf":        len(enfs_unicas),
                "enfermedades": enfs_unicas[:8],
            })

        n_enf_total = sum(c["n_enf"] for c in cultivos_detalle)
        max_exp     = max((c["exportacion"] for c in cultivos_detalle), default=0)

        estados.append({
            "estado":          estado,
            "lat":             coords["lat"],
            "lon":             coords["lon"],
            "cultivos":        cultivos_detalle,
            "n_cultivos":      len(cultivos_detalle),
            "n_enfermedades":  n_enf_total,
            "max_exportacion": max_exp,
        })

    return estados


# ─── HTML ─────────────────────────────────────────────────────────────────────
def generar_html(estados, output=OUTPUT_HTML):
    datos_json  = json.dumps(estados, ensure_ascii=False)
    colores_json = json.dumps(COLORES_CULTIVO, ensure_ascii=False)
    todos_cultivos = sorted(COLORES_CULTIVO.keys())

    options_cultivos = '<option value="todos">🌾 Todos los cultivos</option>\n'
    for c in todos_cultivos:
        color = COLORES_CULTIVO.get(c, "#95a5a6")
        label = c.replace("(", "").replace(")", "").replace(",", "").title()[:30]
        options_cultivos += f'<option value="{c}" data-color="{color}">{label}</option>\n'

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agrobotanix — Mapa de Cultivos</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif; background:#1a1a2e; }}

        .header {{
            background:linear-gradient(135deg,#1a3c2e 0%,#2d6a4f 60%,#1a3c2e 100%);
            color:white; padding:14px 24px;
            display:flex; align-items:center; justify-content:space-between;
            box-shadow:0 3px 12px rgba(0,0,0,0.4);
        }}
        .header-left {{ display:flex; align-items:center; gap:12px; }}
        .header-title {{ font-size:1.45em; font-weight:700; letter-spacing:0.5px; }}
        .header-sub {{ font-size:0.8em; color:#95d5b2; margin-top:2px; }}
        .header-stats {{ display:flex; gap:24px; }}
        .hstat {{ text-align:center; }}
        .hstat-val {{ font-size:1.4em; font-weight:700; color:#74c69d; }}
        .hstat-lbl {{ font-size:0.7em; color:#b7e4c7; text-transform:uppercase; letter-spacing:0.5px; }}

        .filtros {{
            background:#0d1b2a; padding:10px 20px;
            display:flex; gap:12px; align-items:center; flex-wrap:wrap;
            border-bottom:2px solid #2d6a4f;
        }}
        .filtros label {{ color:#95d5b2; font-size:0.8em; font-weight:600; text-transform:uppercase; }}
        .filtros select {{
            background:#1e3a5f; color:white; border:1px solid #2d6a4f;
            padding:6px 12px; border-radius:6px; font-size:0.86em; cursor:pointer;
            min-width:210px;
        }}
        .filtros select:hover {{ border-color:#74c69d; }}
        .filtros select option {{ background:#1e3a5f; }}
        .btn-reset {{
            background:#7b2d00; color:#ffd6a5; border:1px solid #e17055;
            padding:6px 14px; border-radius:6px; font-size:0.82em;
            cursor:pointer; font-weight:600; margin-left:auto;
        }}
        .btn-reset:hover {{ background:#a93226; color:white; }}

        .main-layout {{ display:flex; height:calc(100vh - 112px); }}
        #map {{ flex:1; }}

        .side-panel {{
            width:340px; background:#0d1b2a; overflow-y:auto;
            border-left:2px solid #1e3a5f; display:flex; flex-direction:column;
        }}
        .side-panel::-webkit-scrollbar {{ width:5px; }}
        .side-panel::-webkit-scrollbar-thumb {{ background:#2d6a4f; border-radius:3px; }}

        .panel-section {{ padding:14px; border-bottom:1px solid #1e3a5f; }}
        .panel-title {{
            color:#74c69d; font-size:0.75em; font-weight:700;
            text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;
        }}

        #estado-detalle {{ padding:14px; flex:1; }}
        .panel-placeholder {{
            display:flex; flex-direction:column; align-items:center;
            justify-content:center; color:#2d6a4f;
            padding:40px 20px; text-align:center; height:100%;
        }}
        .panel-placeholder .icon {{ font-size:3em; margin-bottom:14px; opacity:0.6; }}
        .panel-placeholder p {{ font-size:0.82em; line-height:1.7; color:#3d7a5e; }}

        .estado-header {{
            background:linear-gradient(135deg,#1a3c2e,#2d6a4f);
            border-radius:8px; padding:12px 14px; margin-bottom:10px; color:white;
        }}
        .estado-nombre {{ font-size:1.1em; font-weight:700; }}
        .estado-badges {{ display:flex; gap:6px; flex-wrap:wrap; margin-top:6px; }}
        .badge {{
            padding:2px 8px; border-radius:10px; font-size:0.7em; font-weight:600;
        }}
        .badge-cultivos {{ background:#2d6a4f; color:#d8f3dc; }}
        .badge-enf       {{ background:#7b2d00; color:#ffd6a5; }}
        .badge-exp       {{ background:#1a3c5e; color:#aed6f1; }}

        .cultivo-card {{
            background:#1e3a5f; border-radius:7px; padding:9px 11px;
            margin-bottom:7px; border-left:4px solid;
        }}
        .cultivo-nombre {{
            font-weight:700; color:white; font-size:0.87em;
            display:flex; align-items:center; justify-content:space-between;
        }}
        .cultivo-exp {{ font-size:0.72em; color:#95d5b2; margin-top:1px; }}
        .enf-list {{ margin-top:7px; }}
        .enf-item {{
            background:#0d1b2a; border-radius:4px; padding:5px 8px;
            margin-bottom:4px;
        }}
        .enf-nombre {{ color:#e2e8f0; font-weight:600; font-size:0.74em; margin-bottom:3px; }}
        .enf-meta {{ display:flex; gap:5px; flex-wrap:wrap; margin-bottom:3px; }}
        .tag {{
            padding:1px 6px; border-radius:8px; font-size:0.66em; font-weight:600;
        }}
        .tag-hongos   {{ background:#6b3fa0; color:#e9d8fd; }}
        .tag-virus    {{ background:#9b2335; color:#ffd6d6; }}
        .tag-bacterias {{ background:#1a5276; color:#aed6f1; }}
        .tag-alta  {{ background:#7b2d00; color:#ffd6a5; }}
        .tag-media {{ background:#7d5a00; color:#fff3cd; }}
        .tag-baja  {{ background:#1a4731; color:#d8f3dc; }}
        .prod-row {{ display:flex; gap:5px; flex-wrap:wrap; }}
        .prod-pill {{
            padding:2px 7px; border-radius:9px; font-size:0.67em; font-weight:700;
        }}
        .prod-prev {{ background:#1a4731; color:#74c69d; border:1px solid #2d6a4f; }}
        .prod-corr {{ background:#4a1942; color:#f7aef8; border:1px solid #7b2d8b; }}
        .more-enf {{ font-size:0.7em; color:#74c69d; padding:3px 0 0 2px; }}

        .leyenda-cultivos {{ display:flex; flex-direction:column; gap:4px; }}
        .leyenda-item {{
            display:flex; align-items:center; gap:8px; font-size:0.77em;
            color:#b0c4de; cursor:pointer; padding:3px 5px; border-radius:4px;
            transition:background 0.15s;
        }}
        .leyenda-item:hover {{ background:#1e3a5f; color:white; }}
        .leyenda-item.inactivo {{ opacity:0.3; }}
        .leyenda-dot {{
            width:10px; height:10px; border-radius:50%; flex-shrink:0;
            border:1.5px solid rgba(255,255,255,0.25);
        }}

        /* Leyenda de vista en el mapa */
        .map-legend {{
            background:#0d1b2a; border:1px solid #2d6a4f; border-radius:7px;
            padding:10px 13px; font-size:0.76em; color:#b0c4de;
        }}
        .map-legend-title {{
            color:#74c69d; font-weight:700; margin-bottom:7px;
            font-size:0.8em; text-transform:uppercase; letter-spacing:0.5px;
        }}
        .map-legend-item {{ display:flex; align-items:center; gap:7px; margin:3px 0; }}
        .map-legend-dot {{
            width:12px; height:12px; border-radius:50%; flex-shrink:0;
        }}

        .leaflet-tooltip {{
            background:#0d1b2a !important; border:1px solid #2d6a4f !important;
            color:#e2e8f0 !important; border-radius:6px !important;
            font-size:12px !important; padding:8px 12px !important;
            box-shadow:0 4px 14px rgba(0,0,0,0.6) !important;
            max-width:280px !important;
        }}
        .leaflet-tooltip-top:before {{ border-top-color:#2d6a4f !important; }}
    </style>
</head>
<body>

<div class="header">
    <div class="header-left">
        <span style="font-size:26px;">🌱</span>
        <div>
            <div class="header-title">Agrobotanix</div>
            <div class="header-sub">Mapa fitosanitario — cultivos, enfermedades y productos</div>
        </div>
    </div>
    <div class="header-stats">
        <div class="hstat"><div class="hstat-val" id="stat-estados">—</div><div class="hstat-lbl">Estados</div></div>
        <div class="hstat"><div class="hstat-val" id="stat-cultivos">—</div><div class="hstat-lbl">Cultivos</div></div>
        <div class="hstat"><div class="hstat-val" id="stat-enf">—</div><div class="hstat-lbl">Reg. enf.</div></div>
    </div>
</div>

<div class="filtros">
    <label>Cultivo</label>
    <select id="sel-cultivo">
        {options_cultivos}
    </select>
    <label style="margin-left:8px;">Vista del mapa</label>
    <select id="sel-vista">
        <option value="cultivos">🌾 Densidad de cultivos</option>
        <option value="exportacion">📦 Potencial exportación</option>
        <option value="enfermedades">🦠 Riesgo fitosanitario</option>
    </select>
    <button class="btn-reset" onclick="resetFiltros()">✕ Reset</button>
</div>

<div class="main-layout">
    <div id="map"></div>
    <div class="side-panel">
        <div id="estado-detalle">
            <div class="panel-placeholder">
                <div class="icon">🗺️</div>
                <p>Haz clic en un estado del mapa para ver cultivos, enfermedades y productos fitosanitarios recomendados.</p>
            </div>
        </div>
        <div class="panel-section">
            <div class="panel-title">Cultivos — clic para filtrar</div>
            <div class="leyenda-cultivos" id="leyenda"></div>
        </div>
    </div>
</div>

<script>
const DATOS  = {datos_json};
const COLORES = {colores_json};

let map, legendControl;
let markers      = [];
let cultivoFiltro = 'todos';
let vistaActual   = 'cultivos';

// ── Init ───────────────────────────────────────────────────────────────────
window.onload = () => {{
    map = L.map('map', {{zoomControl:true}}).setView([23.5,-102.0],5);
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{
        attribution:'© CartoDB', subdomains:'abcd', maxZoom:19
    }}).addTo(map);

    renderLeyenda();
    renderMarcadores();
}};

// ── Color helpers ──────────────────────────────────────────────────────────
function colorPorCultivos(n) {{
    if (n <= 1) return '#74b9ff';
    if (n <= 3) return '#00b894';
    if (n <= 5) return '#fdcb6e';
    return '#e17055';
}}
function colorPorExportacion(p) {{
    if (p < 20)  return '#74b9ff';
    if (p < 40)  return '#55efc4';
    if (p < 60)  return '#fdcb6e';
    if (p < 75)  return '#e17055';
    return '#d63031';
}}
function colorPorEnfermedades(n) {{
    if (n < 5)  return '#55efc4';
    if (n < 10) return '#fdcb6e';
    if (n < 20) return '#e17055';
    return '#d63031';
}}
function getPctCultivoFiltrado(e) {{
    if (cultivoFiltro === 'todos') return 0;
    const c = e.cultivos.find(c => c.nombre === cultivoFiltro);
    return c ? c.exportacion : 0;
}}
function getColor(e) {{
    if (vistaActual === 'cultivos')     return colorPorCultivos(e.n_cultivos);
    if (vistaActual === 'exportacion')  return colorPorExportacion(getPctCultivoFiltrado(e));
    if (vistaActual === 'enfermedades') return colorPorEnfermedades(e.n_enfermedades);
    return '#74c69d';
}}
function getRadius(e) {{
    if (vistaActual === 'cultivos')     return 10 + e.n_cultivos * 3;
    if (vistaActual === 'exportacion')  return 10 + (getPctCultivoFiltrado(e) / 100) * 28;
    if (vistaActual === 'enfermedades') return 10 + Math.min(e.n_enfermedades * 1.3, 32);
    return 14;
}}

// ── Tooltip ────────────────────────────────────────────────────────────────
function buildTooltip(e) {{
    const cultivos = cultivoFiltro === 'todos'
        ? e.cultivos : e.cultivos.filter(c => c.nombre === cultivoFiltro);
    const dots = cultivos.map(c =>
        `<span style="display:inline-block;width:8px;height:8px;background:${{c.color}};
         border-radius:50%;margin-right:4px;vertical-align:middle;"></span>${{cap(c.nombre)}}`
    ).join('<br>');

    let expLine = '';
    if (vistaActual === 'exportacion' && cultivoFiltro !== 'todos') {{
        const pct = getPctCultivoFiltrado(e);
        expLine = `<br><span style="color:#aed6f1">📦 ${{cap(cultivoFiltro)}}: <b>${{pct}}%</b> va a exportación</span>`;
    }}

    return `<b style="font-size:13px">${{cap(e.estado)}}</b><br>
        <span style="color:#74c69d">🌾 ${{cultivos.length}} cultivo(s)</span><br>
        ${{dots}}<br>
        <span style="color:#ffd6a5">🦠 ${{e.n_enfermedades}} reg. fitosanitarios</span>
        ${{expLine}}`;
}}

// ── Marcadores ─────────────────────────────────────────────────────────────
function renderMarcadores() {{
    markers.forEach(m => map.removeLayer(m));
    markers = [];

    // Vista exportacion sin cultivo seleccionado → pedir al usuario que filtre
    if (vistaActual === 'exportacion' && cultivoFiltro === 'todos') {{
        document.getElementById('estado-detalle').innerHTML = `
            <div class="panel-placeholder">
                <div class="icon">📦</div>
                <p>Selecciona un <b style="color:#74c69d">cultivo</b> en el filtro superior para ver su porcentaje de exportación por estado.</p>
            </div>`;
        actualizarLeyendaMapa();
        return;
    }}

    let datos = DATOS;
    if (cultivoFiltro !== 'todos') {{
        datos = datos.filter(e => e.cultivos.some(c => c.nombre === cultivoFiltro));
    }}

    datos.forEach(estado => {{
        const color  = getColor(estado);
        const radius = getRadius(estado);

        const circle = L.circleMarker([estado.lat, estado.lon], {{
            radius, fillColor:color,
            color:'white', weight:1.5,
            opacity:1, fillOpacity:0.85,
        }});

        circle.bindTooltip(buildTooltip(estado), {{direction:'top', offset:[0,-radius]}});
        circle.on('click', () => mostrarDetalle(estado));
        circle.addTo(map);
        markers.push(circle);
    }});

    actualizarStats(datos);
    actualizarLeyendaMapa();
}}

// ── Panel detalle ──────────────────────────────────────────────────────────
function mostrarDetalle(e) {{
    const cultivos = cultivoFiltro === 'todos'
        ? e.cultivos : e.cultivos.filter(c => c.nombre === cultivoFiltro);

    let html = `
    <div class="estado-header">
        <div class="estado-nombre">📍 ${{cap(e.estado)}}</div>
        <div class="estado-badges">
            <span class="badge badge-cultivos">🌾 ${{cultivos.length}} cultivos</span>
            <span class="badge badge-enf">🦠 ${{e.n_enfermedades}} enfermedades</span>
            <span class="badge badge-exp">📦 ${{e.max_exportacion}}% exp. máx.</span>
        </div>
    </div>`;

    cultivos.forEach(c => {{
        const enfs = c.enfermedades.slice(0,5);
        let enfsHtml = '';
        if (enfs.length) {{
            enfsHtml = '<div class="enf-list">' + enfs.map(enf => {{
                const tt = 'tag-' + enf.tipo.toLowerCase().trim();
                const td = 'tag-' + enf.dificultad.toLowerCase().trim();
                return `<div class="enf-item">
                    <div class="enf-nombre">🦠 ${{enf.nombre}}</div>
                    <div class="enf-meta">
                        <span class="tag ${{tt}}">${{enf.tipo}}</span>
                        <span class="tag ${{td}}">${{enf.dificultad}}</span>
                    </div>
                    <div class="prod-row">
                        <span class="prod-pill prod-prev">🛡️ ${{enf.preventivo}}</span>
                        <span class="prod-pill prod-corr">💊 ${{enf.correctivo}}</span>
                    </div>
                </div>`;
            }}).join('') + '</div>';
            if (c.n_enf > 5)
                enfsHtml += `<div class="more-enf">+ ${{c.n_enf-5}} enfermedades más...</div>`;
        }}

        html += `<div class="cultivo-card" style="border-left-color:${{c.color}}">
            <div class="cultivo-nombre">
                <span>
                    <span style="display:inline-block;width:9px;height:9px;
                        background:${{c.color}};border-radius:50%;margin-right:5px;"></span>
                    ${{cap(c.nombre)}}
                </span>
                <span style="font-size:0.72em;color:#95d5b2;">📦 ${{c.exportacion}}%</span>
            </div>
            <div class="cultivo-exp">🦠 ${{c.n_enf}} enfermedades</div>
            ${{enfsHtml}}
        </div>`;
    }});

    document.getElementById('estado-detalle').innerHTML = html;
}}

// ── Leyenda panel ──────────────────────────────────────────────────────────
function renderLeyenda() {{
    const cont = document.getElementById('leyenda');
    const cultivos = [...new Set(DATOS.flatMap(e => e.cultivos.map(c => c.nombre)))].sort();
    cont.innerHTML = cultivos.map(c => {{
        const color = COLORES[c] || '#95a5a6';
        const id    = 'ley-' + c.replace(/[^a-z]/g,'_');
        return `<div class="leyenda-item" id="${{id}}" onclick="filtrarCultivo('${{c}}')">
            <div class="leyenda-dot" style="background:${{color}};"></div>
            <span>${{cap(c)}}</span>
        </div>`;
    }}).join('');
}}

function filtrarCultivo(nombre) {{
    cultivoFiltro = (cultivoFiltro === nombre) ? 'todos' : nombre;
    document.getElementById('sel-cultivo').value = cultivoFiltro;
    syncLeyenda();
    renderMarcadores();
}}

function syncLeyenda() {{
    document.querySelectorAll('.leyenda-item').forEach(el => {{
        const activo = cultivoFiltro === 'todos'
            || el.id === 'ley-' + cultivoFiltro.replace(/[^a-z]/g,'_');
        el.classList.toggle('inactivo', !activo);
    }});
}}

// ── Leyenda del mapa ──────────────────────────────────────────────────────
function actualizarLeyendaMapa() {{
    if (legendControl) map.removeControl(legendControl);
    legendControl = L.control({{position:'bottomleft'}});
    legendControl.onAdd = function() {{
        const div = L.DomUtil.create('div','map-legend');
        let items = '';
        if (vistaActual === 'cultivos') {{
            div.innerHTML = `<div class="map-legend-title">🌾 Cultivos por estado</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#74b9ff"></div>1–2 cultivos</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#00b894"></div>3–4 cultivos</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#fdcb6e"></div>5–6 cultivos</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#e17055"></div>7+ cultivos</div>`;
        }} else if (vistaActual === 'exportacion') {{
            const nombreCultivo = cultivoFiltro !== 'todos' ? cap(cultivoFiltro) : null;
            div.innerHTML = nombreCultivo
                ? `<div class="map-legend-title">📦 Exportación — ${{nombreCultivo}}</div>
                   <div class="map-legend-item"><div class="map-legend-dot" style="background:#74b9ff"></div>&lt;20%</div>
                   <div class="map-legend-item"><div class="map-legend-dot" style="background:#55efc4"></div>20–40%</div>
                   <div class="map-legend-item"><div class="map-legend-dot" style="background:#fdcb6e"></div>40–60%</div>
                   <div class="map-legend-item"><div class="map-legend-dot" style="background:#e17055"></div>60–75%</div>
                   <div class="map-legend-item"><div class="map-legend-dot" style="background:#d63031"></div>&gt;75%</div>`
                : `<div class="map-legend-title">📦 Exportación</div>
                   <div style="font-size:0.78em;color:#74c69d;margin-top:4px;line-height:1.5;">
                     Selecciona un cultivo<br>para ver su % de exportación
                   </div>`;
        }} else {{
            div.innerHTML = `<div class="map-legend-title">🦠 Riesgo fitosanitario</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#55efc4"></div>&lt;5 registros</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#fdcb6e"></div>5–10</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#e17055"></div>10–20</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#d63031"></div>20+</div>`;
        }}
        return div;
    }};
    legendControl.addTo(map);
}}

// ── Stats ──────────────────────────────────────────────────────────────────
function actualizarStats(datos) {{
    const d = datos || DATOS;
    document.getElementById('stat-estados').textContent  = d.length;
    document.getElementById('stat-cultivos').textContent = new Set(d.flatMap(e=>e.cultivos.map(c=>c.nombre))).size;
    document.getElementById('stat-enf').textContent      = d.reduce((s,e)=>s+e.n_enfermedades,0);
}}

// ── Eventos ────────────────────────────────────────────────────────────────
document.getElementById('sel-cultivo').addEventListener('change', e => {{
    cultivoFiltro = e.target.value;
    syncLeyenda();
    renderMarcadores();
}});
document.getElementById('sel-vista').addEventListener('change', e => {{
    vistaActual = e.target.value;
    renderMarcadores();
}});

function resetFiltros() {{
    cultivoFiltro = 'todos';
    vistaActual   = 'cultivos';
    document.getElementById('sel-cultivo').value = 'todos';
    document.getElementById('sel-vista').value   = 'cultivos';
    syncLeyenda();
    renderMarcadores();
    document.getElementById('estado-detalle').innerHTML = `
        <div class="panel-placeholder">
            <div class="icon">🗺️</div>
            <p>Haz clic en un estado del mapa para ver cultivos, enfermedades y productos fitosanitarios recomendados.</p>
        </div>`;
}}

// ── Util ───────────────────────────────────────────────────────────────────
function cap(s) {{
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
}}
</script>
</body>
</html>"""

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML generado: {output}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("📂 Cargando datos...")
    enfermedades, calendario, exportacion = cargar_datos()
    print(f"   ✅ {len(enfermedades)} enfermedades | {len(calendario)} registros")

    print("🔄 Procesando datos por estado...")
    estados = construir_datos_estados(calendario, enfermedades, exportacion)
    print(f"   ✅ {len(estados)} estados con datos")

    print("🎨 Generando HTML con Leaflet...")
    generar_html(estados)
    print(f"\n✅ Listo. Abre {OUTPUT_HTML} en tu navegador.")


if __name__ == "__main__":
    main()
