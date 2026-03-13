# python3 generar_dashboard.py

import json
import re
import pandas as pd
from collections import defaultdict

# ─── Rutas ────────────────────────────────────────────────────────────────────
EXCEL_PATH  = "master_db_agrobotanix.xlsx"
OUTPUT_HTML = "dashboard_agrobotanix.html"

# ─── Coordenadas ─────────────────────────────────────────────────────────────
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

# ─── Meses (para fenológico) ──────────────────────────────────────────────────
MESES_NOMBRES = [
    'enero','febrero','marzo','abril','mayo','junio',
    'julio','agosto','septiembre','octubre','noviembre','diciembre'
]

# ─── Normalización dificultad ─────────────────────────────────────────────────
def normalizar_dificultad(valor):
    if pd.isna(valor):
        return "media"
    v = str(valor).strip().lower()
    if v in ("alta", "alto"):                              return "alta"
    if v in ("media–alta", "media-alta", "medio-alto"):   return "media-alta"
    if v in ("media", "medio"):                            return "media"
    if v in ("baja–media", "baja-media", "bajo-medio"):   return "baja-media"
    if v in ("baja", "bajo"):                              return "baja"
    return "media"


# ─── Helpers fenológico ───────────────────────────────────────────────────────
def _mes_a_num(s):
    """Convierte nombre de mes a índice 0-based. Tolera typos comunes."""
    s = s.strip().lower()
    s = s.replace('febreo', 'febrero').replace('agosoto', 'agosto')
    for i, m in enumerate(MESES_NOMBRES):
        if s.startswith(m[:3]):
            return i
    return None


def _parse_rango_meses(texto):
    """Devuelve lista de índices 0-based de meses activos a partir de texto libre."""
    if not texto or str(texto).strip() in ('', 'nan', 'None'):
        return []
    texto = str(texto).strip().lower()
    resultado = set()
    partes = re.split(r'[,;]', texto)
    for parte in partes:
        parte = parte.strip()
        segmentos = re.split(r'[-–]', parte)
        if len(segmentos) == 2:
            ini = _mes_a_num(segmentos[0])
            fin = _mes_a_num(segmentos[1])
            if ini is not None and fin is not None:
                if fin >= ini:
                    for x in range(ini, fin + 1):
                        resultado.add(x)
                else:                          # cruza año: ej. agosto-marzo
                    for x in list(range(ini, 12)) + list(range(0, fin + 1)):
                        resultado.add(x)
        elif len(segmentos) == 1:
            idx = _mes_a_num(segmentos[0])
            if idx is not None:
                resultado.add(idx)
    return sorted(resultado)


def _normalizar_modalidad(s):
    if not s or str(s).strip() in ('', 'nan'):
        return ''
    s = str(s).strip()
    if 'Riego' in s and 'Temporal' in s:
        return 'Riego - Temporal'
    elif 'Riego' in s:
        return 'Riego'
    elif 'Temporal' in s:
        return 'Temporal'
    return s.strip()


def _to_num(v):
    """Convierte a float; si es rango '150-180' toma el promedio."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    m = re.match(r'(\d+)\s*[-–]\s*(\d+)', s)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2
    try:
        return float(s)
    except ValueError:
        return None


# ─── Carga de datos ───────────────────────────────────────────────────────────
def cargar_datos():
    xl = pd.read_excel(EXCEL_PATH, sheet_name=None)
    enfermedades = xl["tbl_enfermedades"].copy()
    calendario   = xl["tbl_cultivo_calendario"]
    exportacion  = xl["tbl_cultivo_exportacion"][["cultivo", "pct_exportacion"]].dropna()
    etapas       = xl["tbl_etapas_fenologicas"]          # ← NUEVO
    enfermedades["dificultad_erradicacion"] = enfermedades["dificultad_erradicacion"].apply(normalizar_dificultad)
    return enfermedades, calendario, exportacion, etapas  # ← etapas agregado


# ─── Datos mapa ───────────────────────────────────────────────────────────────
def construir_datos_mapa(calendario, enfermedades, exportacion):
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
            "cientifico": str(row["nombre_cientifico"]),
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
            pct_exp     = exp_map.get(c, 0)
            enfs        = enf_por_cultivo.get(c, [])
            enfs_unicas = list({e["nombre"]: e for e in enfs}.values())
            cultivos_detalle.append({
                "nombre":       c,
                "color":        COLORES_CULTIVO.get(c, "#95a5a6"),
                "exportacion":  round(float(pct_exp) * 100, 1),
                "n_enf":        len(enfs_unicas),
                "enfermedades": enfs_unicas,
            })
        n_enf_total = sum(c["n_enf"] for c in cultivos_detalle)
        max_exp     = max((c["exportacion"] for c in cultivos_detalle), default=0)
        estados.append({
            "estado": estado, "lat": coords["lat"], "lon": coords["lon"],
            "cultivos": cultivos_detalle, "n_cultivos": len(cultivos_detalle),
            "n_enfermedades": n_enf_total, "max_exportacion": max_exp,
        })
    return estados


# ─── Datos enfermedades ───────────────────────────────────────────────────────
def construir_datos_enfermedades(enfermedades):
    registros = []
    for _, row in enfermedades.iterrows():
        registros.append({
            "cultivo":           str(row["cultivo"]).strip(),
            "problema":          str(row["problema_fitosanitario"]).strip(),
            "nombre_comun":      str(row["nombre_comun"]).strip(),
            "nombre_cientifico": str(row["nombre_cientifico"]).strip(),
            "sintomas":          str(row["sintomas"]).strip(),
            "tipo_patogeno":     str(row["tipo_patogeno"]).strip(),
            "region_enf":        str(row["region_enfermedad"]).strip(),
            "dificultad":        str(row["dificultad_erradicacion"]).strip(),
            "region_pais":       str(row["region_del_pais"]).strip(),
            "preventivo":        str(row["producto_preventivo"]).strip(),
            "dosis_prev":        str(row["dosis_preventivo"]).strip(),
            "frec_prev":         str(row["frecuencia_preventivo"]).strip(),
            "correctivo":        str(row["producto_correctivo"]).strip(),
            "dosis_corr":        str(row["dosis_correctivo"]).strip(),
            "frec_corr":         str(row["frecuencia_correctivo"]).strip(),
            "postcosecha":       str(row["producto_postcosecha"]).strip(),
            "color":             COLORES_CULTIVO.get(str(row["cultivo"]).strip(), "#95a5a6"),
        })
    return registros


# ─── Datos fenológico (NUEVO) ─────────────────────────────────────────────────
def construir_datos_fenologicos(calendario, etapas_df):
    """
    Normaliza tbl_cultivo_calendario y tbl_etapas_fenologicas y devuelve
    un dict con dos claves: 'calendario' y 'etapas'.
    """
    # ── Calendario ────────────────────────────────────────────────────────────
    cal_data = defaultdict(dict)
    for _, row in calendario.iterrows():
        cultivo = str(row["cultivo"]).strip() if pd.notna(row["cultivo"]) else None
        estado  = str(row["estado"]).strip().lower() if pd.notna(row["estado"]) else None
        if not cultivo or not estado:
            continue
        cal_data[cultivo][estado] = {
            "mes_siembra":   _parse_rango_meses(row.get("mes_siembra")),
            "mes_cosecha":   _parse_rango_meses(row.get("mes_cosecha")),
            "ciclo":         str(row.get("ciclo", "") or "").strip(),
            "modalidad":     _normalizar_modalidad(row.get("modalidad")),
            "meses_lluvia":  _parse_rango_meses(row.get("meses_lluvia")),
            "meses_secas":   _parse_rango_meses(row.get("meses_secas")),
        }

    # ── Etapas fenológicas ────────────────────────────────────────────────────
    # Solo usar columnas A-G (índices 0-6); ignorar H en adelante (notas del jr.)
    cols_utiles = list(etapas_df.columns[:7])
    etapas_limpia = etapas_df[cols_utiles].copy()
    etapas_limpia.columns = [
        'cultivo', 'etapa', 'orden_etapa',
        'dias_inicio', 'dias_fin', 'descripcion', 'caracteristicas'
    ]

    eta_data = defaultdict(list)
    for _, row in etapas_limpia.iterrows():
        cultivo_raw = row['cultivo']
        etapa_raw   = row['etapa']
        if pd.isna(cultivo_raw) or pd.isna(etapa_raw):
            continue

        # Renombrar Chile pimiento → pimienta
        cultivo = 'pimienta' if str(cultivo_raw).strip() == 'Chile pimiento' \
                  else str(cultivo_raw).strip()

        di = _to_num(row['dias_inicio'])
        df = _to_num(row['dias_fin'])

        eta_data[cultivo].append({
            "etapa":          str(etapa_raw).strip().capitalize(),
            "orden":          int(row['orden_etapa']) if pd.notna(row['orden_etapa']) else 99,
            "dias_inicio":    int(di) if di is not None else 0,
            "dias_fin":       int(df) if df is not None else 0,
            "descripcion":    str(row['descripcion']).strip() if pd.notna(row['descripcion']) else '',
            "caracteristicas":str(row['caracteristicas']).strip() if pd.notna(row['caracteristicas']) else '',
        })

    # Ordenar etapas por orden_etapa
    for c in eta_data:
        eta_data[c] = sorted(eta_data[c], key=lambda x: x["orden"])

    return {
        "calendario": {k: dict(v) for k, v in cal_data.items()},
        "etapas":     dict(eta_data),
    }


# ─── HTML ─────────────────────────────────────────────────────────────────────
def generar_html(estados_mapa, registros_enf, datos_feno, output=OUTPUT_HTML):
    datos_mapa_json = json.dumps(estados_mapa, ensure_ascii=False)
    datos_enf_json  = json.dumps(registros_enf, ensure_ascii=False)
    datos_feno_json = json.dumps(datos_feno, ensure_ascii=False)   # ← NUEVO
    colores_json    = json.dumps(COLORES_CULTIVO, ensure_ascii=False)

    todos_cultivos  = sorted(COLORES_CULTIVO.keys())
    cultivos_enf    = sorted(set(r["cultivo"] for r in registros_enf))

    opts_mapa = '<option value="todos">🌾 Todos los cultivos</option>\n'
    for c in todos_cultivos:
        label = c.replace("(","").replace(")","").replace(",","").title()[:30]
        opts_mapa += f'<option value="{c}">{label}</option>\n'

    opts_enf = '<option value="todos">🌾 Todos los cultivos</option>\n'
    for c in cultivos_enf:
        label = c.replace("(","").replace(")","").replace(",","").title()[:32]
        opts_enf += f'<option value="{c}">{label}</option>\n'

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agrobotanix — Dashboard</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;
                background:#0d1b2a; color:#e2e8f0; height:100vh; overflow:hidden; }}

        /* ══ HEADER ══════════════════════════════════════════════════════════ */
        .header {{
            background:linear-gradient(135deg,#1a3c2e 0%,#2d6a4f 60%,#1a3c2e 100%);
            padding:12px 24px; display:flex; align-items:center;
            justify-content:space-between; box-shadow:0 3px 12px rgba(0,0,0,0.5);
            height:56px;
        }}
        .header-left {{ display:flex; align-items:center; gap:12px; }}
        .header-title {{ font-size:1.35em; font-weight:700; color:white; }}
        .header-sub {{ font-size:0.75em; color:#95d5b2; }}
        .header-stats {{ display:flex; gap:22px; }}
        .hstat {{ text-align:center; }}
        .hstat-val {{ font-size:1.3em; font-weight:700; color:#74c69d; line-height:1; }}
        .hstat-lbl {{ font-size:0.62em; color:#b7e4c7; text-transform:uppercase; letter-spacing:0.5px; }}

        /* ══ TABS ════════════════════════════════════════════════════════════ */
        .tab-bar {{
            background:#0a1628; display:flex; border-bottom:2px solid #2d6a4f;
            height:42px;
        }}
        .tab {{
            padding:0 26px; cursor:pointer; font-size:0.88em; font-weight:600;
            color:#4a7a9b; border-bottom:3px solid transparent; margin-bottom:-2px;
            display:flex; align-items:center; gap:7px; transition:all 0.2s;
            user-select:none;
        }}
        .tab:hover {{ color:#74c69d; background:rgba(45,106,79,0.1); }}
        .tab.activo {{ color:#74c69d; border-bottom-color:#74c69d; background:rgba(45,106,79,0.15); }}
        .tab-badge {{
            background:#2d6a4f; color:#d8f3dc; padding:1px 7px;
            border-radius:10px; font-size:0.72em; font-weight:700;
        }}

        /* ══ CONTENIDO TABS ══════════════════════════════════════════════════ */
        .tab-content {{ display:none; height:calc(100vh - 98px); }}
        .tab-content.activo {{ display:flex; flex-direction:column; }}

        /* ══ FILTROS (compartido) ════════════════════════════════════════════ */
        .filtros {{
            background:#0a1628; padding:8px 18px;
            display:flex; gap:10px; align-items:center; flex-wrap:wrap;
            border-bottom:1px solid #1e3a5f; flex-shrink:0;
        }}
        .filtros label {{ color:#95d5b2; font-size:0.76em; font-weight:600; text-transform:uppercase; }}
        .filtros select {{
            background:#1e3a5f; color:white; border:1px solid #2d6a4f;
            padding:5px 10px; border-radius:5px; font-size:0.82em; cursor:pointer;
        }}
        .filtros select:hover {{ border-color:#74c69d; }}
        .filtros select option {{ background:#1e3a5f; }}
        .filtros input[type=text] {{
            background:#1e3a5f; color:white; border:1px solid #2d6a4f;
            padding:5px 10px; border-radius:5px; font-size:0.82em;
            min-width:190px; outline:none;
        }}
        .filtros input[type=text]::placeholder {{ color:#4a7a9b; }}
        .filtros input[type=text]:focus {{ border-color:#74c69d; }}
        .btn-reset {{
            background:#7b2d00; color:#ffd6a5; border:1px solid #e17055;
            padding:5px 12px; border-radius:5px; font-size:0.8em;
            cursor:pointer; font-weight:600; margin-left:auto;
        }}
        .btn-reset:hover {{ background:#a93226; color:white; }}

        /* ══ TAB 1 — MAPA ════════════════════════════════════════════════════ */
        .mapa-layout {{ display:flex; flex:1; overflow:hidden; }}
        #map {{ flex:1; }}

        .mapa-side {{
            width:320px; background:#0a1628; overflow-y:auto;
            border-left:2px solid #1e3a5f; flex-shrink:0;
        }}
        .mapa-side::-webkit-scrollbar {{ width:5px; }}
        .mapa-side::-webkit-scrollbar-thumb {{ background:#2d6a4f; border-radius:3px; }}

        .side-section {{ padding:13px; border-bottom:1px solid #1e3a5f; }}
        .side-title {{
            color:#74c69d; font-size:0.72em; font-weight:700;
            text-transform:uppercase; letter-spacing:1px; margin-bottom:9px;
        }}

        .panel-placeholder {{
            display:flex; flex-direction:column; align-items:center;
            justify-content:center; padding:36px 18px; text-align:center;
        }}
        .panel-placeholder .icon {{ font-size:2.4em; margin-bottom:12px; opacity:0.45; }}
        .panel-placeholder p {{ font-size:0.79em; line-height:1.7; color:#3d7a5e; }}

        .estado-header {{
            background:linear-gradient(135deg,#1a3c2e,#2d6a4f);
            border-radius:7px; padding:11px 13px; margin-bottom:9px; color:white;
        }}
        .estado-nombre {{ font-size:1.05em; font-weight:700; }}
        .estado-badges {{ display:flex; gap:5px; flex-wrap:wrap; margin-top:5px; }}
        .badge {{ padding:2px 7px; border-radius:9px; font-size:0.68em; font-weight:600; }}
        .badge-cultivos {{ background:#2d6a4f; color:#d8f3dc; }}
        .badge-enf       {{ background:#7b2d00; color:#ffd6a5; }}
        .badge-exp       {{ background:#1a3c5e; color:#aed6f1; }}

        .cultivo-card {{
            background:#1e3a5f; border-radius:6px; padding:8px 10px;
            margin-bottom:6px; border-left:4px solid;
        }}
        .cultivo-nombre {{
            font-weight:700; color:white; font-size:0.85em;
            display:flex; align-items:center; justify-content:space-between;
        }}
        .cultivo-exp {{ font-size:0.7em; color:#95d5b2; margin-top:1px; }}

        .enf-toggle {{
            display:flex; align-items:center; justify-content:space-between;
            margin-top:7px; padding:5px 7px;
            background:#0d1b2a; border-radius:5px;
            cursor:pointer; border:1px solid #1e3a5f;
            transition:border-color 0.15s, background 0.15s;
            user-select:none;
        }}
        .enf-toggle:hover {{ border-color:#2d6a4f; background:#111f30; }}
        .enf-toggle-label {{ font-size:0.72em; color:#74c69d; font-weight:600; }}
        .enf-toggle-icon {{
            font-size:0.68em; color:#4a7a9b;
            transition:transform 0.2s; display:inline-block;
        }}
        .enf-toggle-icon.abierto {{ transform:rotate(90deg); }}
        .enf-list {{ margin-top:5px; display:none; }}
        .enf-list.visible {{ display:block; }}

        .enf-item {{
            background:#0d1b2a; border-radius:4px; padding:5px 7px; margin-bottom:3px;
        }}
        .enf-nombre {{ color:#e2e8f0; font-weight:600; font-size:0.73em; margin-bottom:1px; }}
        .enf-cientifico {{ color:#4a7a9b; font-style:italic; font-size:0.67em; margin-bottom:3px; }}
        .enf-meta {{ display:flex; gap:4px; flex-wrap:wrap; margin-bottom:3px; }}
        .prod-row {{ display:flex; gap:4px; flex-wrap:wrap; }}
        .prod-pill {{ padding:1px 7px; border-radius:9px; font-size:0.66em; font-weight:700; }}
        .prod-prev {{ background:#1a4731; color:#74c69d; border:1px solid #2d6a4f; }}
        .prod-corr {{ background:#4a1942; color:#f7aef8; border:1px solid #7b2d8b; }}

        .leyenda-cultivos {{ display:flex; flex-direction:column; gap:3px; }}
        .leyenda-item {{
            display:flex; align-items:center; gap:7px; font-size:0.75em;
            color:#b0c4de; cursor:pointer; padding:3px 5px; border-radius:4px;
            transition:background 0.12s;
        }}
        .leyenda-item:hover {{ background:#1e3a5f; color:white; }}
        .leyenda-item.inactivo {{ opacity:0.28; }}
        .leyenda-dot {{ width:9px; height:9px; border-radius:50%; flex-shrink:0; border:1.5px solid rgba(255,255,255,0.2); }}

        .map-legend {{
            background:#0d1b2a; border:1px solid #2d6a4f; border-radius:6px;
            padding:9px 12px; font-size:0.74em; color:#b0c4de;
        }}
        .map-legend-title {{ color:#74c69d; font-weight:700; margin-bottom:6px; font-size:0.78em; text-transform:uppercase; }}
        .map-legend-item {{ display:flex; align-items:center; gap:6px; margin:3px 0; }}
        .map-legend-dot {{ width:11px; height:11px; border-radius:50%; flex-shrink:0; }}

        .leaflet-tooltip {{
            background:#0d1b2a !important; border:1px solid #2d6a4f !important;
            color:#e2e8f0 !important; border-radius:6px !important;
            font-size:12px !important; padding:7px 11px !important;
            box-shadow:0 4px 14px rgba(0,0,0,0.6) !important; max-width:270px !important;
        }}
        .leaflet-tooltip-top:before {{ border-top-color:#2d6a4f !important; }}

        /* ══ TAB 2 — ENFERMEDADES ════════════════════════════════════════════ */
        .enf-layout {{ display:flex; flex:1; overflow:hidden; }}

        .tabla-container {{
            flex:1; overflow-y:auto; overflow-x:auto; background:#0d1b2a;
        }}
        .tabla-container::-webkit-scrollbar {{ width:6px; height:6px; }}
        .tabla-container::-webkit-scrollbar-track {{ background:#0d1b2a; }}
        .tabla-container::-webkit-scrollbar-thumb {{ background:#2d6a4f; border-radius:3px; }}

        table {{ width:100%; border-collapse:collapse; font-size:0.81em; }}
        thead {{ position:sticky; top:0; z-index:10; }}
        thead tr {{ background:#0a1628; }}
        th {{
            padding:9px 11px; text-align:left; font-weight:600; color:#74c69d;
            font-size:0.76em; text-transform:uppercase; letter-spacing:0.5px;
            border-bottom:2px solid #2d6a4f; white-space:nowrap;
            cursor:pointer; user-select:none;
        }}
        th:hover {{ color:#b7e4c7; }}
        th.sorted {{ color:#d8f3dc; }}
        tbody tr {{ border-bottom:1px solid #1e3a5f; transition:background 0.1s; cursor:pointer; }}
        tbody tr:hover {{ background:#1a2d45; }}
        tbody tr.seleccionada {{ background:#1e3a5f !important; }}
        td {{ padding:8px 11px; vertical-align:middle; }}
        .td-cultivo {{ white-space:nowrap; }}
        .cultivo-dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:5px; vertical-align:middle; }}
        .td-cientifico {{ color:#6b7a8d; font-style:italic; font-size:0.88em; }}
        .td-sintomas {{ max-width:200px; }}
        .sintomas-texto {{ display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; color:#9aa5b4; font-size:0.88em; }}

        .tag {{ display:inline-block; padding:2px 7px; border-radius:9px; font-size:0.72em; font-weight:600; white-space:nowrap; }}
        .tag-hongos    {{ background:#3d1f6e; color:#d8b4fe; }}
        .tag-virus     {{ background:#6b1a2a; color:#fca5a5; }}
        .tag-bacterias {{ background:#1a3a5c; color:#93c5fd; }}
        .tag-alta      {{ background:#7b2d00; color:#ffd6a5; }}
        .tag-media-alta {{ background:#5c3800; color:#fde68a; }}
        .tag-media     {{ background:#4a3800; color:#fef08a; }}
        .tag-baja-media {{ background:#1a4031; color:#6ee7b7; }}
        .tag-baja      {{ background:#14532d; color:#86efac; }}

        .prod-cell {{ min-width:120px; }}
        .prod-nombre {{ font-weight:700; font-size:0.8em; margin-bottom:1px; }}
        .prod-prev-nombre {{ color:#74c69d; }}
        .prod-corr-nombre {{ color:#f7aef8; }}
        .prod-post-nombre {{ color:#93c5fd; }}
        .prod-dosis {{ font-size:0.72em; color:#6b7a8d; line-height:1.3; }}
        .prod-frec  {{ font-size:0.68em; color:#4a7a9b; margin-top:1px; }}

        .enf-side {{
            width:290px; background:#0a1628; border-left:2px solid #1e3a5f;
            overflow-y:auto; flex-shrink:0;
        }}
        .enf-side::-webkit-scrollbar {{ width:5px; }}
        .enf-side::-webkit-scrollbar-thumb {{ background:#2d6a4f; border-radius:3px; }}

        .stat-grande {{ font-size:2em; font-weight:700; color:#74c69d; line-height:1; margin-bottom:3px; }}
        .stat-lbl {{ font-size:0.72em; color:#4a7a9b; }}
        .dist-item {{ margin-bottom:9px; }}
        .dist-label {{ display:flex; justify-content:space-between; font-size:0.74em; color:#b0c4de; margin-bottom:2px; }}
        .dist-bar-bg {{ background:#1e3a5f; border-radius:3px; height:6px; overflow:hidden; }}
        .dist-bar {{ height:100%; border-radius:3px; transition:width 0.35s ease; }}

        .enf-detalle-header {{
            background:linear-gradient(135deg,#1a3c2e,#2d6a4f);
            border-radius:6px; padding:10px 12px; margin-bottom:9px;
        }}
        .enf-detalle-nombre {{ font-weight:700; font-size:0.92em; margin-bottom:2px; }}
        .enf-detalle-cient  {{ font-style:italic; font-size:0.75em; color:#95d5b2; }}
        .enf-detalle-bloque {{
            background:#1e3a5f; border-radius:5px; padding:9px 11px; margin-bottom:7px; font-size:0.78em;
        }}
        .enf-detalle-bloque-title {{
            font-size:0.68em; font-weight:700; color:#74c69d;
            text-transform:uppercase; letter-spacing:0.5px; margin-bottom:5px;
        }}
        .enf-detalle-texto {{ color:#b0c4de; line-height:1.5; }}
        .prod-detalle-pill {{
            display:inline-block; padding:2px 9px; border-radius:8px;
            font-size:0.78em; font-weight:700; margin-bottom:4px;
        }}
        .sin-resultados {{ padding:50px 25px; text-align:center; color:#2d6a4f; font-size:0.88em; }}

        /* ══ TAB 3 — CALENDARIO FENOLÓGICO ══════════════════════════════════ */
        .feno-layout {{
            display:grid;
            grid-template-columns:280px 1fr;
            flex:1;
            overflow:hidden;
        }}

        /* Sidebar fenológico */
        .feno-sidebar {{
            border-right:1px solid #1e3a5f;
            display:flex; flex-direction:column; overflow:hidden;
            background:#0a1628;
        }}
        .feno-search {{
            padding:12px; border-bottom:1px solid #1e3a5f; position:relative;
        }}
        .feno-search input {{
            width:100%; background:#1e3a5f; border:1px solid #2d6a4f;
            border-radius:6px; padding:7px 10px 7px 30px;
            color:#e2e8f0; font-family:'Segoe UI',sans-serif; font-size:0.82em; outline:none;
            transition:border-color 0.2s;
        }}
        .feno-search input:focus {{ border-color:#74c69d; }}
        .feno-search input::placeholder {{ color:#4a7a9b; }}
        .feno-search-icon {{
            position:absolute; left:22px; top:50%;
            transform:translateY(-50%); color:#4a7a9b; font-size:13px; pointer-events:none;
        }}
        .feno-cultivo-list {{ overflow-y:auto; flex:1; padding:6px; }}
        .feno-cultivo-list::-webkit-scrollbar {{ width:4px; }}
        .feno-cultivo-list::-webkit-scrollbar-thumb {{ background:#1e3a5f; border-radius:2px; }}

        .feno-cultivo-item {{
            display:flex; align-items:center; gap:9px;
            padding:8px 10px; border-radius:6px; cursor:pointer;
            transition:background 0.15s; border:1px solid transparent;
        }}
        .feno-cultivo-item:hover {{ background:#1e3a5f; }}
        .feno-cultivo-item.active {{
            background:rgba(45,106,79,0.25); border-color:rgba(116,198,157,0.3);
        }}
        .feno-cultivo-dot {{
            width:8px; height:8px; border-radius:50%; flex-shrink:0;
        }}
        .feno-cultivo-name {{ font-size:0.82em; color:#b0c4de; line-height:1.3; }}
        .feno-cultivo-item.active .feno-cultivo-name {{ color:#74c69d; }}

        /* Ficha lateral */
        .feno-ficha {{
            border-top:1px solid #1e3a5f; padding:13px; background:#0d1b2a;
        }}
        .feno-ficha-title {{
            font-size:0.65em; font-weight:700; color:#4a7a9b;
            text-transform:uppercase; letter-spacing:1px; margin-bottom:9px;
        }}
        .feno-badge {{
            display:inline-flex; align-items:center; gap:5px;
            background:#1e3a5f; border:1px solid #2d6a4f; border-radius:14px;
            padding:3px 9px; font-size:0.72em; color:#b0c4de; margin:2px 2px;
        }}
        .feno-badge .dot {{ width:6px; height:6px; border-radius:50%; }}
        .feno-badges {{ margin-bottom:10px; }}

        .feno-strip-label {{
            font-size:0.65em; color:#4a7a9b; font-weight:600;
            text-transform:uppercase; letter-spacing:0.5px; margin-bottom:3px;
        }}
        .feno-meses-strip {{
            display:grid; grid-template-columns:repeat(12,1fr); gap:2px; margin-bottom:6px;
        }}
        .feno-mes-cell {{
            height:16px; border-radius:2px; background:#1e3a5f;
        }}
        .feno-mes-cell.lluvia  {{ background:rgba(59,130,246,0.5); border:1px solid rgba(59,130,246,0.65); }}
        .feno-mes-cell.secas   {{ background:rgba(245,158,11,0.4); border:1px solid rgba(245,158,11,0.55); }}
        .feno-mes-cell.siembra {{ background:rgba(116,198,157,0.55); border:1px solid rgba(116,198,157,0.75); }}
        .feno-mes-cell.cosecha {{ background:rgba(244,114,182,0.45); border:1px solid rgba(244,114,182,0.65); }}
        .feno-mes-abr {{
            font-size:7px; color:#2d5a3d; text-align:center; margin-top:1px;
        }}
        .feno-strip-legend {{
            display:flex; flex-wrap:wrap; gap:8px; margin-top:4px;
        }}
        .feno-legend-item {{
            display:flex; align-items:center; gap:4px; font-size:0.68em; color:#4a7a9b;
        }}
        .feno-legend-chip {{ width:10px; height:10px; border-radius:2px; }}
        .feno-datos-pend {{
            font-size:0.68em; color:#2d5a3d; font-style:italic; margin-top:5px;
        }}

        /* Panel derecho fenológico */
        .feno-main {{ display:flex; flex-direction:column; overflow:hidden; background:#0d1b2a; }}

        .feno-view-tabs {{
            display:flex; border-bottom:1px solid #1e3a5f; padding:0 18px; flex-shrink:0;
            background:#0a1628;
        }}
        .feno-view-tab {{
            font-size:0.76em; font-weight:600; color:#4a7a9b;
            padding:11px 14px; cursor:pointer;
            border-bottom:2px solid transparent; transition:color 0.2s, border-color 0.2s;
            white-space:nowrap; text-transform:uppercase; letter-spacing:0.5px;
        }}
        .feno-view-tab:hover {{ color:#b0c4de; }}
        .feno-view-tab.active {{ color:#74c69d; border-bottom-color:#74c69d; }}

        .feno-view-panel {{ display:none; flex:1; overflow:auto; padding:18px 22px; }}
        .feno-view-panel.active {{ display:block; }}

        /* Empty states */
        .feno-empty {{
            display:flex; flex-direction:column; align-items:center;
            justify-content:center; height:100%; color:#2d5a3d; gap:10px;
        }}
        .feno-empty .icon {{ font-size:36px; }}
        .feno-empty p {{ font-size:0.82em; }}

        /* Gantt */
        .feno-gantt-header {{ margin-bottom:16px; }}
        .feno-gantt-title {{
            font-size:0.72em; font-weight:700; color:#4a7a9b;
            text-transform:uppercase; letter-spacing:0.8px;
        }}
        .feno-gantt-sub {{ font-size:0.75em; color:#2d5a3d; margin-top:3px; }}

        .feno-gantt-wrap {{
            background:#0a1628; border:1px solid #1e3a5f; border-radius:8px; overflow:hidden;
        }}
        .feno-gantt-row {{
            display:grid; grid-template-columns:190px 1fr 90px;
            align-items:center; padding:0 14px; border-bottom:1px solid #1e3a5f;
            min-height:48px; gap:10px;
        }}
        .feno-gantt-row:last-child {{ border-bottom:none; }}
        .feno-gantt-row:hover {{ background:#111f30; }}

        .feno-gantt-label {{ font-size:0.8em; color:#b0c4de; font-weight:600; }}
        .feno-gantt-label small {{
            display:block; font-size:0.82em; color:#4a7a9b;
            margin-top:1px; font-weight:400;
        }}
        .feno-gantt-track {{
            height:24px; background:#1e3a5f; border-radius:5px; position:relative;
        }}
        .feno-gantt-bar {{
            position:absolute; height:100%; border-radius:5px;
            display:flex; align-items:center; padding:0 6px;
            font-size:9px; color:rgba(0,0,0,0.75); font-weight:700;
            white-space:nowrap; overflow:hidden; cursor:pointer;
            transition:filter 0.15s, transform 0.1s;
        }}
        .feno-gantt-bar:hover {{ filter:brightness(1.18); transform:scaleY(1.06); }}
        .feno-gantt-days {{
            font-size:0.7em; color:#4a7a9b; text-align:right; white-space:nowrap;
        }}
        .feno-axis {{
            display:grid; grid-template-columns:190px 1fr 90px;
            padding:6px 14px 0; gap:10px;
        }}
        .feno-axis-labels {{
            display:flex; justify-content:space-between;
            font-size:0.65em; color:#2d5a3d;
        }}

        /* Tooltip Gantt */
        .feno-tooltip {{
            position:fixed; background:#0a1628; border:1px solid #2d6a4f;
            border-radius:8px; padding:11px 13px; max-width:250px;
            pointer-events:none; z-index:9999; display:none;
            box-shadow:0 6px 24px rgba(0,0,0,0.6);
        }}
        .feno-tooltip.visible {{ display:block; }}
        .feno-tt-etapa {{ font-size:0.72em; color:#74c69d; font-weight:700; letter-spacing:0.06em; margin-bottom:5px; }}
        .feno-tt-desc  {{ font-size:0.78em; color:#b0c4de; margin-bottom:3px; }}
        .feno-tt-car   {{ font-size:0.72em; color:#6b7a8d; }}
        .feno-tt-dias  {{
            margin-top:7px; font-size:0.68em; color:#4a7a9b;
            border-top:1px solid #1e3a5f; padding-top:5px;
        }}

        /* Tabla meses por estado */
        .feno-mapa-title {{
            font-size:0.72em; font-weight:700; color:#4a7a9b;
            text-transform:uppercase; letter-spacing:0.8px; margin-bottom:14px;
        }}
        .feno-mapa-wrap {{
            background:#0a1628; border:1px solid #1e3a5f; border-radius:8px; overflow:hidden;
        }}
        .feno-table {{ width:100%; border-collapse:collapse; }}
        .feno-table th {{
            font-size:0.65em; color:#4a7a9b; text-transform:uppercase;
            padding:8px 3px; text-align:center; border-bottom:1px solid #1e3a5f;
            background:#0d1b2a; letter-spacing:0.05em; cursor:default;
        }}
        .feno-table th.estado-col {{
            text-align:left; padding-left:14px; min-width:120px;
        }}
        .feno-table td {{ padding:2px 3px; border-bottom:1px solid rgba(30,58,95,0.5); }}
        .feno-table tr:last-child td {{ border-bottom:none; }}
        .feno-table tr:hover td {{ background:#111f30; }}
        .feno-estado-td {{
            font-size:0.78em; color:#6b7a8d; padding:6px 6px 6px 14px;
            text-transform:capitalize; white-space:nowrap;
        }}
        .feno-mes-td {{ width:38px; height:28px; border-radius:3px; }}
        .feno-cell-lluvia  {{ background:rgba(59,130,246,0.28); }}
        .feno-cell-secas   {{ background:rgba(245,158,11,0.22); }}
        .feno-cell-siembra {{ background:rgba(116,198,157,0.38); }}
        .feno-cell-cosecha {{ background:rgba(244,114,182,0.35); }}
        .feno-cell-chips {{
            display:flex; flex-direction:column; gap:2px;
            width:100%; height:100%; padding:2px 2px; border-radius:3px;
        }}
        .feno-chip {{ flex:1; border-radius:2px; }}
        .feno-chip-lluvia  {{ background:rgba(59,130,246,0.55); }}
        .feno-chip-secas   {{ background:rgba(245,158,11,0.5); }}
        .feno-chip-siembra {{ background:rgba(116,198,157,0.65); }}
        .feno-chip-cosecha {{ background:rgba(244,114,182,0.6); }}
        .feno-mapa-legend {{
            display:flex; flex-wrap:wrap; gap:14px;
            padding:11px 14px; border-top:1px solid #1e3a5f; background:#0d1b2a;
        }}
        .feno-mapa-legend-item {{
            display:flex; align-items:center; gap:5px;
            font-size:0.72em; color:#4a7a9b;
        }}
        .feno-legend-sq {{ width:12px; height:12px; border-radius:2px; }}

        /* Colores de etapas (reutiliza paleta dashboard) */
        .ec0  {{ background:#74c69d; }}
        .ec1  {{ background:#06b6d4; }}
        .ec2  {{ background:#818cf8; }}
        .ec3  {{ background:#f472b6; }}
        .ec4  {{ background:#fb923c; }}
        .ec5  {{ background:#facc15; }}
        .ec6  {{ background:#a78bfa; }}
        .ec7  {{ background:#38bdf8; }}
        .ec8  {{ background:#4ade80; }}
        .ec9  {{ background:#f87171; }}
        .ec10 {{ background:#e879f9; }}
        .ec11 {{ background:#34d399; }}
    </style>
</head>
<body>

<!-- ══ HEADER ══════════════════════════════════════════════════════════════ -->
<div class="header">
    <div class="header-left">
        <span style="font-size:24px;">🌱</span>
        <div>
            <div class="header-title">Agrobotanix</div>
            <div class="header-sub">Dashboard fitosanitario de cultivos en México</div>
        </div>
    </div>
    <div class="header-stats">
        <div class="hstat"><div class="hstat-val">{len(estados_mapa)}</div><div class="hstat-lbl">Estados</div></div>
        <div class="hstat"><div class="hstat-val">{len(COLORES_CULTIVO)}</div><div class="hstat-lbl">Cultivos</div></div>
        <div class="hstat"><div class="hstat-val">{len(registros_enf)}</div><div class="hstat-lbl">Registros enf.</div></div>
    </div>
</div>

<!-- ══ TABS ════════════════════════════════════════════════════════════════ -->
<div class="tab-bar">
    <div class="tab activo" id="tab-mapa" onclick="cambiarTab('mapa')">
        🗺️ Mapa de cultivos
        <span class="tab-badge">{len(estados_mapa)}</span>
    </div>
    <div class="tab" id="tab-enfermedades" onclick="cambiarTab('enfermedades')">
        🦠 Enfermedades
        <span class="tab-badge">{len(registros_enf)}</span>
    </div>
    <div class="tab" id="tab-calendario" onclick="cambiarTab('calendario')">
        📅 Calendario fenológico
        <span class="tab-badge">{len(COLORES_CULTIVO)}</span>
    </div>
</div>

<!-- ══════════════════════════════════════════════════════════════════════════
     TAB 1 — MAPA
═══════════════════════════════════════════════════════════════════════════ -->
<div class="tab-content activo" id="content-mapa">
    <div class="filtros">
        <label>Cultivo</label>
        <select id="m-sel-cultivo">{opts_mapa}</select>
        <label style="margin-left:6px;">Vista</label>
        <select id="m-sel-vista">
            <option value="cultivos">🌾 Densidad de cultivos</option>
            <option value="exportacion">📦 Potencial exportación</option>
            <option value="enfermedades">🦠 Riesgo fitosanitario</option>
        </select>
        <button class="btn-reset" onclick="mapaReset()">✕ Reset</button>
    </div>
    <div class="mapa-layout">
        <div id="map"></div>
        <div class="mapa-side">
            <div id="estado-detalle">
                <div class="panel-placeholder">
                    <div class="icon">🗺️</div>
                    <p>Haz clic en un estado para ver cultivos, enfermedades y productos recomendados.</p>
                </div>
            </div>
            <div class="side-section">
                <div class="side-title">Cultivos — clic para filtrar</div>
                <div class="leyenda-cultivos" id="mapa-leyenda"></div>
            </div>
        </div>
    </div>
</div>

<!-- ══════════════════════════════════════════════════════════════════════════
     TAB 2 — ENFERMEDADES
═══════════════════════════════════════════════════════════════════════════ -->
<div class="tab-content" id="content-enfermedades">
    <div class="filtros">
        <label>Cultivo</label>
        <select id="e-sel-cultivo">{opts_enf}</select>
        <label>Patógeno</label>
        <select id="e-sel-patogeno">
            <option value="todos">Todos</option>
            <option value="hongos">🍄 Hongos</option>
            <option value="virus">🧬 Virus</option>
            <option value="bacterias">🔬 Bacterias</option>
        </select>
        <label>Dificultad</label>
        <select id="e-sel-dificultad">
            <option value="todos">Todas</option>
            <option value="alta">🔴 Alta</option>
            <option value="media-alta">🟠 Media-Alta</option>
            <option value="media">🟡 Media</option>
            <option value="baja-media">🟢 Baja-Media</option>
            <option value="baja">🟢 Baja</option>
        </select>
        <label>Buscar</label>
        <input type="text" id="e-buscador" placeholder="Nombre, síntoma, región...">
        <div style="margin-left:auto;display:flex;align-items:center;gap:16px;">
            <span style="font-size:0.78em;color:#4a7a9b;">
                🍄 <span id="e-stat-hongos">—</span> hongos &nbsp;
                🧬 <span id="e-stat-virus">—</span> virus &nbsp;
                🔬 <span id="e-stat-bacterias">—</span> bacterias
            </span>
            <button class="btn-reset" onclick="enfReset()">✕ Reset</button>
        </div>
    </div>
    <div class="enf-layout">
        <div class="tabla-container">
            <table id="tabla-enf">
                <thead>
                    <tr>
                        <th onclick="enfOrdenar('cultivo')">Cultivo</th>
                        <th onclick="enfOrdenar('nombre_comun')">Enfermedad</th>
                        <th>Nombre científico</th>
                        <th onclick="enfOrdenar('tipo_patogeno')">Patógeno</th>
                        <th onclick="enfOrdenar('dificultad')">Dificultad</th>
                        <th>Región afectada</th>
                        <th>Síntomas</th>
                        <th>🛡️ Preventivo</th>
                        <th>💊 Correctivo</th>
                        <th>📦 Postcosecha</th>
                    </tr>
                </thead>
                <tbody id="enf-tbody"></tbody>
            </table>
            <div id="enf-sin-resultados" class="sin-resultados" style="display:none;">
                😔 No se encontraron enfermedades con los filtros seleccionados.
            </div>
        </div>
        <div class="enf-side">
            <div class="side-section">
                <div class="side-title">📊 Resumen filtrado</div>
                <div class="stat-grande" id="e-stat-total">—</div>
                <div class="stat-lbl">enfermedades visibles</div>
            </div>
            <div class="side-section">
                <div class="side-title">Por tipo de patógeno</div>
                <div id="e-dist-patogeno"></div>
            </div>
            <div class="side-section">
                <div class="side-title">Por dificultad de erradicación</div>
                <div id="e-dist-dificultad"></div>
            </div>
            <div class="side-section" id="enf-panel-detalle">
                <div class="panel-placeholder">
                    <div class="icon">🔬</div>
                    <p>Haz clic en una fila para ver el detalle completo.</p>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- ══════════════════════════════════════════════════════════════════════════
     TAB 3 — CALENDARIO FENOLÓGICO
═══════════════════════════════════════════════════════════════════════════ -->
<div class="tab-content" id="content-calendario">
    <div class="feno-layout">

        <!-- Sidebar -->
        <div class="feno-sidebar">
            <div class="feno-search">
                <span class="feno-search-icon">🔍</span>
                <input type="text" id="fenoSearch" placeholder="Buscar cultivo..."
                       oninput="fenoFiltrarLista()">
            </div>
            <div class="feno-cultivo-list" id="fenoCultivoList"></div>
            <div class="feno-ficha" id="fenoFicha" style="display:none">
                <div class="feno-ficha-title">Ficha del cultivo</div>
                <div class="feno-badges" id="fenoBadges"></div>
                <div class="feno-strip-label">Temporadas · Lluvia / Secas</div>
                <div class="feno-meses-strip" id="fenoStripLS"></div>
                <div class="feno-strip-label" id="fenoStripSCLabel" style="display:none">Siembra / Cosecha</div>
                <div class="feno-meses-strip" id="fenoStripSC" style="display:none"></div>
                <div class="feno-strip-legend">
                    <div class="feno-legend-item">
                        <span class="feno-legend-chip" style="background:rgba(59,130,246,0.5)"></span>Lluvia
                    </div>
                    <div class="feno-legend-item">
                        <span class="feno-legend-chip" style="background:rgba(245,158,11,0.45)"></span>Secas
                    </div>
                    <div class="feno-legend-item" id="fenoLegSiembra" style="display:none">
                        <span class="feno-legend-chip" style="background:rgba(116,198,157,0.6)"></span>Siembra
                    </div>
                    <div class="feno-legend-item" id="fenoLegCosecha" style="display:none">
                        <span class="feno-legend-chip" style="background:rgba(244,114,182,0.5)"></span>Cosecha
                    </div>
                </div>
                <div class="feno-datos-pend" id="fenoDatosPend"></div>
            </div>
        </div>

        <!-- Panel derecho -->
        <div class="feno-main">
            <div class="feno-view-tabs">
                <div class="feno-view-tab active" onclick="fenoSwitchView('gantt',this)">
                    📊 Timeline Fenológico
                </div>
                <div class="feno-view-tab" onclick="fenoSwitchView('meses',this)">
                    📅 Siembra / Cosecha por Estado
                </div>
            </div>

            <!-- Vista Gantt -->
            <div class="feno-view-panel active" id="feno-panel-gantt">
                <div class="feno-empty" id="fenoEmptyGantt">
                    <div class="icon">🌿</div>
                    <p>Selecciona un cultivo para ver sus etapas fenológicas</p>
                </div>
                <div id="fenoGanttContent" style="display:none">
                    <div class="feno-gantt-header">
                        <div class="feno-gantt-title" id="fenoGanttTitulo"></div>
                        <div class="feno-gantt-sub"   id="fenoGanttSub"></div>
                    </div>
                    <div class="feno-axis">
                        <div></div>
                        <div class="feno-axis-labels" id="fenoAxisLabels"></div>
                        <div></div>
                    </div>
                    <div class="feno-gantt-wrap" id="fenoGanttWrap"></div>
                </div>
            </div>

            <!-- Vista Meses por Estado -->
            <div class="feno-view-panel" id="feno-panel-meses">
                <div class="feno-empty" id="fenoEmptyMeses">
                    <div class="icon">🗺️</div>
                    <p>Selecciona un cultivo para ver el calendario por estado</p>
                </div>
                <div id="fenoMesesContent" style="display:none">
                    <div class="feno-mapa-title" id="fenoMesesTitulo"></div>
                    <div class="feno-mapa-wrap">
                        <table class="feno-table" id="fenoMesesTable"></table>
                        <div class="feno-mapa-legend">
                            <div class="feno-mapa-legend-item">
                                <div class="feno-legend-sq" style="background:rgba(59,130,246,0.45)"></div>Lluvia
                            </div>
                            <div class="feno-mapa-legend-item">
                                <div class="feno-legend-sq" style="background:rgba(245,158,11,0.4)"></div>Secas
                            </div>
                            <div class="feno-mapa-legend-item">
                                <div class="feno-legend-sq" style="background:rgba(116,198,157,0.5)"></div>Siembra
                            </div>
                            <div class="feno-mapa-legend-item">
                                <div class="feno-legend-sq" style="background:rgba(244,114,182,0.45)"></div>Cosecha
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Tooltip Gantt -->
<div class="feno-tooltip" id="fenoTooltip">
    <div class="feno-tt-etapa" id="fttEtapa"></div>
    <div class="feno-tt-desc"  id="fttDesc"></div>
    <div class="feno-tt-car"   id="fttCar"></div>
    <div class="feno-tt-dias"  id="fttDias"></div>
</div>

<script>
// ══ DATOS ══════════════════════════════════════════════════════════════════
const DATOS_MAPA = {datos_mapa_json};
const DATOS_ENF  = {datos_enf_json};
const DATOS_FENO = {datos_feno_json};
const COLORES    = {colores_json};

// ══ TABS ═══════════════════════════════════════════════════════════════════
let mapaIniciado = false;
let fenoIniciado = false;

function cambiarTab(nombre) {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('activo'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('activo'));
    document.getElementById('tab-' + nombre).classList.add('activo');
    document.getElementById('content-' + nombre).classList.add('activo');

    if (nombre === 'mapa' && !mapaIniciado) {{
        setTimeout(iniciarMapa, 50);
        mapaIniciado = true;
    }}
    if (nombre === 'mapa' && mapaIniciado && map) {{
        setTimeout(() => map.invalidateSize(), 50);
    }}
    if (nombre === 'calendario' && !fenoIniciado) {{
        fenoInit();
        fenoIniciado = true;
    }}
}}

// ══════════════════════════════════════════════════════════════════════════
// TAB 1 — MAPA
// ══════════════════════════════════════════════════════════════════════════
let map, legendControl;
let mapa_markers = [];
let mapa_cultivo = 'todos';
let mapa_vista   = 'cultivos';

function iniciarMapa() {{
    map = L.map('map', {{zoomControl:true}}).setView([23.5,-102.0],5);
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{
        attribution:'© CartoDB', subdomains:'abcd', maxZoom:19
    }}).addTo(map);
    renderLeyendaMapa();
    renderMarcadores();
}}

function colorCultivos(n)     {{ return n<=1?'#74b9ff':n<=3?'#00b894':n<=5?'#fdcb6e':'#e17055'; }}
function colorExportacion(p)  {{ return p<20?'#74b9ff':p<40?'#55efc4':p<60?'#fdcb6e':p<75?'#e17055':'#d63031'; }}
function colorEnfermedades(n) {{ return n<5?'#55efc4':n<10?'#fdcb6e':n<20?'#e17055':'#d63031'; }}

function getPctCultivo(e) {{
    if (mapa_cultivo==='todos') return 0;
    const c = e.cultivos.find(c=>c.nombre===mapa_cultivo);
    return c ? c.exportacion : 0;
}}
function getColor(e) {{
    if (mapa_vista==='cultivos')     return colorCultivos(e.n_cultivos);
    if (mapa_vista==='exportacion')  return colorExportacion(getPctCultivo(e));
    if (mapa_vista==='enfermedades') return colorEnfermedades(e.n_enfermedades);
    return '#74c69d';
}}
function getRadius(e) {{
    if (mapa_vista==='cultivos')     return 10+e.n_cultivos*3;
    if (mapa_vista==='exportacion')  return 10+(getPctCultivo(e)/100)*28;
    if (mapa_vista==='enfermedades') return 10+Math.min(e.n_enfermedades*1.3,32);
    return 14;
}}

function buildTooltipMapa(e) {{
    const cs = mapa_cultivo==='todos'?e.cultivos:e.cultivos.filter(c=>c.nombre===mapa_cultivo);
    const dots = cs.map(c=>`<span style="display:inline-block;width:7px;height:7px;background:${{c.color}};border-radius:50%;margin-right:4px;vertical-align:middle;"></span>${{cap(c.nombre)}}`).join('<br>');
    let expLine='';
    if (mapa_vista==='exportacion' && mapa_cultivo!=='todos') {{
        expLine=`<br><span style="color:#aed6f1">📦 ${{cap(mapa_cultivo)}}: <b>${{getPctCultivo(e)}}%</b> exportación</span>`;
    }}
    return `<b style="font-size:13px">${{cap(e.estado)}}</b><br>
        <span style="color:#74c69d">🌾 ${{cs.length}} cultivo(s)</span><br>${{dots}}<br>
        <span style="color:#ffd6a5">🦠 ${{e.n_enfermedades}} reg. fitosanitarios</span>${{expLine}}`;
}}

function renderMarcadores() {{
    mapa_markers.forEach(m=>map.removeLayer(m));
    mapa_markers=[];

    if (mapa_vista==='exportacion' && mapa_cultivo==='todos') {{
        document.getElementById('estado-detalle').innerHTML=`
            <div class="panel-placeholder"><div class="icon">📦</div>
            <p>Selecciona un <b style="color:#74c69d">cultivo</b> para ver su % de exportación por estado.</p></div>`;
        actualizarLeyendaMapa();
        return;
    }}

    let datos = mapa_cultivo==='todos' ? DATOS_MAPA
        : DATOS_MAPA.filter(e=>e.cultivos.some(c=>c.nombre===mapa_cultivo));

    datos.forEach(estado=>{{
        const color=getColor(estado), radius=getRadius(estado);
        const circle=L.circleMarker([estado.lat,estado.lon],{{
            radius,fillColor:color,color:'white',weight:1.5,opacity:1,fillOpacity:0.85
        }});
        circle.bindTooltip(buildTooltipMapa(estado),{{direction:'top',offset:[0,-radius]}});
        circle.on('click',()=>mostrarDetalleEstado(estado));
        circle.addTo(map);
        mapa_markers.push(circle);
    }});
    actualizarLeyendaMapa();
}}

function mostrarDetalleEstado(e) {{
    const cs = mapa_cultivo==='todos'?e.cultivos:e.cultivos.filter(c=>c.nombre===mapa_cultivo);
    let html=`<div class="estado-header">
        <div class="estado-nombre">📍 ${{cap(e.estado)}}</div>
        <div class="estado-badges">
            <span class="badge badge-cultivos">🌾 ${{cs.length}} cultivos</span>
            <span class="badge badge-enf">🦠 ${{e.n_enfermedades}} enf.</span>
            <span class="badge badge-exp">📦 ${{e.max_exportacion}}% exp.</span>
        </div>
    </div>`;

    cs.forEach((c, ci) => {{
        const toggleId=`enf-list-${{ci}}`, iconId=`enf-icon-${{ci}}`;
        let enfsHtml='';
        if (c.enfermedades && c.enfermedades.length) {{
            enfsHtml=c.enfermedades.map(enf=>{{
                const tt='tag-'+enf.tipo.toLowerCase().trim();
                const td='tag-'+enf.dificultad.toLowerCase().trim();
                return `<div class="enf-item">
                    <div class="enf-nombre">🦠 ${{enf.nombre}}</div>
                    <div class="enf-cientifico">(${{enf.cientifico}})</div>
                    <div class="enf-meta">
                        <span class="tag ${{tt}}">${{enf.tipo}}</span>
                        <span class="tag ${{td}}">${{enf.dificultad}}</span>
                    </div>
                    <div class="prod-row">
                        <span class="prod-pill prod-prev">🛡️ ${{enf.preventivo}}</span>
                        <span class="prod-pill prod-corr">💊 ${{enf.correctivo}}</span>
                    </div>
                </div>`;
            }}).join('');
        }}
        html+=`<div class="cultivo-card" style="border-left-color:${{c.color}}">
            <div class="cultivo-nombre">
                <span><span style="display:inline-block;width:8px;height:8px;background:${{c.color}};border-radius:50%;margin-right:5px;"></span>${{cap(c.nombre)}}</span>
                <span style="font-size:0.7em;color:#95d5b2;">📦 ${{c.exportacion}}%</span>
            </div>
            <div class="cultivo-exp">🦠 ${{c.n_enf}} enfermedades</div>
            ${{c.enfermedades && c.enfermedades.length ? `
            <div class="enf-toggle" onclick="toggleEnfList('${{toggleId}}','${{iconId}}')">
                <span class="enf-toggle-label">Ver enfermedades (${{c.n_enf}})</span>
                <span class="enf-toggle-icon" id="${{iconId}}">▶</span>
            </div>
            <div class="enf-list" id="${{toggleId}}">${{enfsHtml}}</div>` : ''}}
        </div>`;
    }});
    document.getElementById('estado-detalle').innerHTML=html;
}}

function toggleEnfList(listId, iconId) {{
    const list=document.getElementById(listId), icon=document.getElementById(iconId);
    if (!list) return;
    const abierto=list.classList.toggle('visible');
    if (icon) icon.classList.toggle('abierto', abierto);
}}

function renderLeyendaMapa() {{
    const cont=document.getElementById('mapa-leyenda');
    const cs=[...new Set(DATOS_MAPA.flatMap(e=>e.cultivos.map(c=>c.nombre)))].sort();
    cont.innerHTML=cs.map(c=>{{
        const color=COLORES[c]||'#95a5a6';
        const id='mley-'+c.replace(/[^a-z]/g,'_');
        return `<div class="leyenda-item" id="${{id}}" onclick="mapaFiltrarCultivo('${{c}}')">
            <div class="leyenda-dot" style="background:${{color}};"></div><span>${{cap(c)}}</span></div>`;
    }}).join('');
}}

function mapaFiltrarCultivo(nombre) {{
    mapa_cultivo=(mapa_cultivo===nombre)?'todos':nombre;
    document.getElementById('m-sel-cultivo').value=mapa_cultivo;
    mapaSyncLeyenda(); renderMarcadores();
}}
function mapaSyncLeyenda() {{
    document.querySelectorAll('.leyenda-item').forEach(el=>{{
        const activo=mapa_cultivo==='todos'||el.id==='mley-'+mapa_cultivo.replace(/[^a-z]/g,'_');
        el.classList.toggle('inactivo',!activo);
    }});
}}
function actualizarLeyendaMapa() {{
    if(legendControl) map.removeControl(legendControl);
    legendControl=L.control({{position:'bottomleft'}});
    legendControl.onAdd=function(){{
        const div=L.DomUtil.create('div','map-legend');
        if(mapa_vista==='cultivos') {{
            div.innerHTML=`<div class="map-legend-title">🌾 Cultivos por estado</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#74b9ff"></div>1–2</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#00b894"></div>3–4</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#fdcb6e"></div>5–6</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#e17055"></div>7+</div>`;
        }} else if(mapa_vista==='exportacion') {{
            const nc=mapa_cultivo!=='todos'?cap(mapa_cultivo):null;
            div.innerHTML=nc
                ?`<div class="map-legend-title">📦 ${{nc}}</div>
                  <div class="map-legend-item"><div class="map-legend-dot" style="background:#74b9ff"></div>&lt;20%</div>
                  <div class="map-legend-item"><div class="map-legend-dot" style="background:#55efc4"></div>20–40%</div>
                  <div class="map-legend-item"><div class="map-legend-dot" style="background:#fdcb6e"></div>40–60%</div>
                  <div class="map-legend-item"><div class="map-legend-dot" style="background:#e17055"></div>60–75%</div>
                  <div class="map-legend-item"><div class="map-legend-dot" style="background:#d63031"></div>&gt;75%</div>`
                :`<div class="map-legend-title">📦 Exportación</div>
                  <div style="font-size:0.76em;color:#74c69d;margin-top:4px;line-height:1.5;">Selecciona un cultivo<br>para ver su % exportación</div>`;
        }} else {{
            div.innerHTML=`<div class="map-legend-title">🦠 Riesgo fitosanitario</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#55efc4"></div>&lt;5</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#fdcb6e"></div>5–10</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#e17055"></div>10–20</div>
            <div class="map-legend-item"><div class="map-legend-dot" style="background:#d63031"></div>20+</div>`;
        }}
        return div;
    }};
    legendControl.addTo(map);
}}

document.getElementById('m-sel-cultivo').addEventListener('change',e=>{{
    mapa_cultivo=e.target.value; mapaSyncLeyenda(); renderMarcadores();
}});
document.getElementById('m-sel-vista').addEventListener('change',e=>{{
    mapa_vista=e.target.value; renderMarcadores();
}});
function mapaReset() {{
    mapa_cultivo='todos'; mapa_vista='cultivos';
    document.getElementById('m-sel-cultivo').value='todos';
    document.getElementById('m-sel-vista').value='cultivos';
    mapaSyncLeyenda(); renderMarcadores();
    document.getElementById('estado-detalle').innerHTML=`
        <div class="panel-placeholder"><div class="icon">🗺️</div>
        <p>Haz clic en un estado para ver cultivos, enfermedades y productos recomendados.</p></div>`;
}}

// ══════════════════════════════════════════════════════════════════════════
// TAB 2 — ENFERMEDADES
// ══════════════════════════════════════════════════════════════════════════
const ORDEN_DIF={{'alta':0,'media-alta':1,'media':2,'baja-media':3,'baja':4}};
let enf_filtrados=[...DATOS_ENF];
let enf_orden_col='cultivo', enf_orden_asc=true;

window.onload=()=>{{
    iniciarMapa();
    mapaIniciado=true;
    enfAplicarFiltros();
    ['e-sel-cultivo','e-sel-patogeno','e-sel-dificultad'].forEach(id=>
        document.getElementById(id).addEventListener('change',enfAplicarFiltros)
    );
    document.getElementById('e-buscador').addEventListener('input',enfAplicarFiltros);
}};

function enfAplicarFiltros() {{
    const cultivo   =document.getElementById('e-sel-cultivo').value;
    const patogeno  =document.getElementById('e-sel-patogeno').value;
    const dificultad=document.getElementById('e-sel-dificultad').value;
    const busqueda  =document.getElementById('e-buscador').value.toLowerCase().trim();
    enf_filtrados=DATOS_ENF.filter(r=>{{
        if(cultivo   !=='todos'&&r.cultivo      !==cultivo)    return false;
        if(patogeno  !=='todos'&&r.tipo_patogeno!==patogeno)   return false;
        if(dificultad!=='todos'&&r.dificultad   !==dificultad) return false;
        if(busqueda&&![r.nombre_comun,r.nombre_cientifico,r.sintomas,r.region_pais,r.region_enf]
            .join(' ').toLowerCase().includes(busqueda)) return false;
        return true;
    }});
    enfOrdenarDatos(); enfRenderTabla(); enfActualizarStats(); enfActualizarDist();
}}

function enfOrdenar(col) {{
    if(enf_orden_col===col) enf_orden_asc=!enf_orden_asc;
    else {{ enf_orden_col=col; enf_orden_asc=true; }}
    document.querySelectorAll('#tabla-enf th').forEach(th=>th.classList.remove('sorted'));
    const map_cols={{'cultivo':0,'nombre_comun':1,'tipo_patogeno':3,'dificultad':4}};
    if(col in map_cols) document.querySelectorAll('#tabla-enf th')[map_cols[col]].classList.add('sorted');
    enfOrdenarDatos(); enfRenderTabla();
}}
function enfOrdenarDatos() {{
    enf_filtrados.sort((a,b)=>{{
        let va=a[enf_orden_col]||'', vb=b[enf_orden_col]||'';
        if(enf_orden_col==='dificultad'){{
            va=ORDEN_DIF[va]??99; vb=ORDEN_DIF[vb]??99;
            return enf_orden_asc?va-vb:vb-va;
        }}
        va=va.toString().toLowerCase(); vb=vb.toString().toLowerCase();
        return enf_orden_asc?va.localeCompare(vb):vb.localeCompare(va);
    }});
}}
function enfRenderTabla() {{
    const tbody=document.getElementById('enf-tbody');
    const sinRes=document.getElementById('enf-sin-resultados');
    if(!enf_filtrados.length){{ tbody.innerHTML=''; sinRes.style.display='block'; return; }}
    sinRes.style.display='none';
    tbody.innerHTML=enf_filtrados.map((r,i)=>{{
        const tt='tag-'+r.tipo_patogeno.toLowerCase();
        const td='tag-'+r.dificultad.toLowerCase();
        const em=r.dificultad==='alta'?'🔴':r.dificultad==='media-alta'?'🟠':r.dificultad==='media'?'🟡':'🟢';
        return `<tr onclick="enfSeleccionarFila(this,${{i}})" data-idx="${{i}}">
            <td class="td-cultivo"><span class="cultivo-dot" style="background:${{r.color}}"></span>${{cap(r.cultivo)}}</td>
            <td><b>${{r.nombre_comun}}</b></td>
            <td class="td-cientifico">${{r.nombre_cientifico}}</td>
            <td><span class="tag ${{tt}}">${{r.tipo_patogeno}}</span></td>
            <td><span class="tag ${{td}}">${{em}} ${{r.dificultad}}</span></td>
            <td style="font-size:0.8em;color:#6b7a8d;max-width:140px;">${{r.region_enf}}</td>
            <td class="td-sintomas"><div class="sintomas-texto" title="${{r.sintomas}}">${{r.sintomas}}</div></td>
            <td class="prod-cell">
                <div class="prod-nombre prod-prev-nombre">🛡️ ${{r.preventivo}}</div>
                <div class="prod-dosis">${{r.dosis_prev}}</div>
                <div class="prod-frec">⏱ ${{r.frec_prev}}</div>
            </td>
            <td class="prod-cell">
                <div class="prod-nombre prod-corr-nombre">💊 ${{r.correctivo}}</div>
                <div class="prod-dosis">${{r.dosis_corr}}</div>
                <div class="prod-frec">⏱ ${{r.frec_corr}}</div>
            </td>
            <td class="prod-cell">
                <div class="prod-nombre prod-post-nombre">📦 ${{r.postcosecha}}</div>
            </td>
        </tr>`;
    }}).join('');
}}
function enfSeleccionarFila(tr,idx) {{
    document.querySelectorAll('#enf-tbody tr').forEach(r=>r.classList.remove('seleccionada'));
    tr.classList.add('seleccionada');
    enfMostrarDetalle(enf_filtrados[idx]);
}}
function enfMostrarDetalle(r) {{
    const tt='tag-'+r.tipo_patogeno.toLowerCase();
    const td='tag-'+r.dificultad.toLowerCase();
    const em=r.dificultad==='alta'?'🔴':r.dificultad==='media-alta'?'🟠':r.dificultad==='media'?'🟡':'🟢';
    document.getElementById('enf-panel-detalle').innerHTML=`
    <div class="side-title">🔬 Detalle</div>
    <div class="enf-detalle-header">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
            <span class="cultivo-dot" style="background:${{r.color}};width:10px;height:10px;"></span>
            <span style="font-size:0.75em;color:#95d5b2;">${{cap(r.cultivo)}}</span>
        </div>
        <div class="enf-detalle-nombre">${{r.nombre_comun}}</div>
        <div class="enf-detalle-cient">${{r.nombre_cientifico}}</div>
        <div style="margin-top:6px;display:flex;gap:5px;flex-wrap:wrap;">
            <span class="tag ${{tt}}">${{r.tipo_patogeno}}</span>
            <span class="tag ${{td}}">${{em}} ${{r.dificultad}}</span>
        </div>
    </div>
    <div class="enf-detalle-bloque">
        <div class="enf-detalle-bloque-title">📍 Región afectada</div>
        <div class="enf-detalle-texto">${{r.region_enf}}</div>
    </div>
    <div class="enf-detalle-bloque">
        <div class="enf-detalle-bloque-title">🌍 Región del país</div>
        <div class="enf-detalle-texto" style="font-size:0.83em;">${{r.region_pais}}</div>
    </div>
    <div class="enf-detalle-bloque">
        <div class="enf-detalle-bloque-title">🔍 Síntomas</div>
        <div class="enf-detalle-texto">${{r.sintomas}}</div>
    </div>
    <div class="enf-detalle-bloque">
        <div class="enf-detalle-bloque-title">🛡️ Preventivo</div>
        <div class="prod-detalle-pill" style="background:#1a4731;color:#74c69d;border:1px solid #2d6a4f;">${{r.preventivo}}</div>
        <div class="enf-detalle-texto" style="margin-top:4px;"><b>Dosis:</b> ${{r.dosis_prev}}<br><b>Frecuencia:</b> ${{r.frec_prev}}</div>
    </div>
    <div class="enf-detalle-bloque">
        <div class="enf-detalle-bloque-title">💊 Correctivo</div>
        <div class="prod-detalle-pill" style="background:#4a1942;color:#f7aef8;border:1px solid #7b2d8b;">${{r.correctivo}}</div>
        <div class="enf-detalle-texto" style="margin-top:4px;"><b>Dosis:</b> ${{r.dosis_corr}}<br><b>Frecuencia:</b> ${{r.frec_corr}}</div>
    </div>
    <div class="enf-detalle-bloque">
        <div class="enf-detalle-bloque-title">📦 Postcosecha</div>
        <div class="prod-detalle-pill" style="background:#1a3c5e;color:#93c5fd;border:1px solid #2563eb;">${{r.postcosecha}}</div>
    </div>`;
}}
function enfActualizarStats() {{
    const t=enf_filtrados.length;
    document.getElementById('e-stat-total').textContent=t;
    document.getElementById('e-stat-hongos').textContent=enf_filtrados.filter(r=>r.tipo_patogeno==='hongos').length;
    document.getElementById('e-stat-virus').textContent=enf_filtrados.filter(r=>r.tipo_patogeno==='virus').length;
    document.getElementById('e-stat-bacterias').textContent=enf_filtrados.filter(r=>r.tipo_patogeno==='bacterias').length;
}}
function enfActualizarDist() {{
    const total=enf_filtrados.length||1;
    document.getElementById('e-dist-patogeno').innerHTML=[
        {{label:'Hongos',key:'hongos',color:'#a78bfa'}},
        {{label:'Virus',key:'virus',color:'#fca5a5'}},
        {{label:'Bacterias',key:'bacterias',color:'#93c5fd'}},
    ].map(p=>{{
        const n=enf_filtrados.filter(r=>r.tipo_patogeno===p.key).length;
        const pct=Math.round(n/total*100);
        return `<div class="dist-item">
            <div class="dist-label"><span>${{p.label}}</span><span>${{n}} (${{pct}}%)</span></div>
            <div class="dist-bar-bg"><div class="dist-bar" style="width:${{pct}}%;background:${{p.color}};"></div></div>
        </div>`;
    }}).join('');
    document.getElementById('e-dist-dificultad').innerHTML=[
        {{label:'Alta',key:'alta',color:'#ef4444'}},
        {{label:'Media-Alta',key:'media-alta',color:'#f97316'}},
        {{label:'Media',key:'media',color:'#eab308'}},
        {{label:'Baja-Media',key:'baja-media',color:'#22c55e'}},
        {{label:'Baja',key:'baja',color:'#16a34a'}},
    ].map(d=>{{
        const n=enf_filtrados.filter(r=>r.dificultad===d.key).length;
        const pct=Math.round(n/total*100);
        if(!n) return '';
        return `<div class="dist-item">
            <div class="dist-label"><span>${{d.label}}</span><span>${{n}} (${{pct}}%)</span></div>
            <div class="dist-bar-bg"><div class="dist-bar" style="width:${{pct}}%;background:${{d.color}};"></div></div>
        </div>`;
    }}).join('');
}}
function enfReset() {{
    ['e-sel-cultivo','e-sel-patogeno','e-sel-dificultad'].forEach(id=>document.getElementById(id).value='todos');
    document.getElementById('e-buscador').value='';
    document.getElementById('enf-panel-detalle').innerHTML=`
        <div class="panel-placeholder"><div class="icon">🔬</div>
        <p>Haz clic en una fila para ver el detalle completo.</p></div>`;
    enfAplicarFiltros();
}}

// ══════════════════════════════════════════════════════════════════════════
// TAB 3 — CALENDARIO FENOLÓGICO
// ══════════════════════════════════════════════════════════════════════════
const FENO_MESES_ABR = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
const FENO_EC = ['ec0','ec1','ec2','ec3','ec4','ec5','ec6','ec7','ec8','ec9','ec10','ec11'];

let fenoCultivoActivo = null;
let fenoVista = 'gantt';
const fenoCultivosOrdenados = Object.keys(DATOS_FENO.calendario).sort();

function fenoInit() {{
    fenoRenderLista(fenoCultivosOrdenados);
    fenoSelectCultivo('aguacate');
}}

function fenoCap(s) {{ return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''; }}

// ── Lista de cultivos ─────────────────────────────────────────────────────
function fenoRenderLista(lista) {{
    const el = document.getElementById('fenoCultivoList');
    el.innerHTML = lista.map(c => {{
        const color = COLORES[c] || '#95a5a6';
        return `<div class="feno-cultivo-item ${{c===fenoCultivoActivo?'active':''}}"
                     onclick="fenoSelectCultivo('${{c}}')">
            <div class="feno-cultivo-dot" style="background:${{color}}"></div>
            <div class="feno-cultivo-name">${{fenoCap(c)}}</div>
        </div>`;
    }}).join('');
}}

function fenoFiltrarLista() {{
    const q = document.getElementById('fenoSearch').value.toLowerCase();
    fenoRenderLista(fenoCultivosOrdenados.filter(c => c.includes(q)));
}}

// ── Selección de cultivo ──────────────────────────────────────────────────
function fenoSelectCultivo(c) {{
    fenoCultivoActivo = c;
    const q = document.getElementById('fenoSearch').value.toLowerCase();
    fenoRenderLista(fenoCultivosOrdenados.filter(x => x.includes(q)));
    fenoRenderFicha(c);
    if (fenoVista === 'gantt') fenoRenderGantt(c);
    else fenoRenderMeses(c);
}}

// ── Ficha lateral ─────────────────────────────────────────────────────────
function fenoRenderFicha(c) {{
    const estados = DATOS_FENO.calendario[c];
    const ficha = document.getElementById('fenoFicha');
    ficha.style.display = 'block';

    const muestra = Object.values(estados)[0];
    const cicloColor = muestra.ciclo.includes('Perenne') ? '#74c69d' :
                       muestra.ciclo.includes('Primavera') ? '#facc15' : '#818cf8';
    const modalColor = muestra.modalidad === 'Riego' ? '#38bdf8' :
                       muestra.modalidad === 'Temporal' ? '#f59e0b' : '#a78bfa';

    document.getElementById('fenoBadges').innerHTML = `
        <div class="feno-badge"><span class="dot" style="background:${{cicloColor}}"></span>${{muestra.ciclo||'N/D'}}</div>
        <div class="feno-badge"><span class="dot" style="background:${{modalColor}}"></span>${{muestra.modalidad||'N/D'}}</div>
    `;

    const allLluvia=new Set(), allSecas=new Set(), allSiem=new Set(), allCos=new Set();
    Object.values(estados).forEach(e=>{{
        e.meses_lluvia.forEach(m=>allLluvia.add(m));
        e.meses_secas.forEach(m=>allSecas.add(m));
        e.mes_siembra.forEach(m=>allSiem.add(m));
        e.mes_cosecha.forEach(m=>allCos.add(m));
    }});

    // Barra lluvia/secas
    document.getElementById('fenoStripLS').innerHTML = FENO_MESES_ABR.map((m,i)=>{{
        const isL=allLluvia.has(i), isS=allSecas.has(i);
        const cls=isL?'lluvia':isS?'secas':'';
        return `<div><div class="feno-mes-cell ${{cls}}" title="${{m}}"></div>
                <div class="feno-mes-abr">${{m[0]}}</div></div>`;
    }}).join('');

    // Barra siembra/cosecha — solo si hay datos
    const hayS=allSiem.size>0, hayC=allCos.size>0;
    const showSC = hayS || hayC;
    document.getElementById('fenoStripSCLabel').style.display = showSC ? '' : 'none';
    document.getElementById('fenoStripSC').style.display      = showSC ? 'grid' : 'none';
    document.getElementById('fenoLegSiembra').style.display   = hayS ? '' : 'none';
    document.getElementById('fenoLegCosecha').style.display   = hayC ? '' : 'none';

    if (showSC) {{
        document.getElementById('fenoStripSC').innerHTML = FENO_MESES_ABR.map((m,i)=>{{
            const isSi=allSiem.has(i), isCo=allCos.has(i);
            const cls=isSi?'siembra':isCo?'cosecha':'';
            return `<div><div class="feno-mes-cell ${{cls}}" title="${{m}}"></div>
                    <div class="feno-mes-abr">${{m[0]}}</div></div>`;
        }}).join('');
    }}

    const faltantes=[];
    if(!hayS) faltantes.push('siembra');
    if(!hayC) faltantes.push('cosecha');
    document.getElementById('fenoDatosPend').textContent =
        faltantes.length ? `* Datos de ${{faltantes.join(' y ')}} pendientes.` : '';
}}

// ── Gantt ─────────────────────────────────────────────────────────────────
function fenoRenderGantt(c) {{
    const etapas = DATOS_FENO.etapas[c];
    document.getElementById('fenoEmptyGantt').style.display    = etapas ? 'none' : 'flex';
    document.getElementById('fenoGanttContent').style.display  = etapas ? 'block' : 'none';
    if (!etapas) return;

    const maxDia = Math.max(...etapas.map(e=>e.dias_fin));
    document.getElementById('fenoGanttTitulo').textContent =
        `Etapas Fenológicas — ${{fenoCap(c)}}`;
    document.getElementById('fenoGanttSub').textContent =
        `${{etapas.length}} etapas · Ciclo total: ${{maxDia}} días`;

    const ticks=6;
    document.getElementById('fenoAxisLabels').innerHTML =
        Array.from({{length:ticks+1}},(_,i)=>`<span>${{Math.round(maxDia*i/ticks)}} d</span>`).join('');

    document.getElementById('fenoGanttWrap').innerHTML = etapas.map((e,idx)=>{{
        const ecClass = FENO_EC[idx % FENO_EC.length];
        const left  = (e.dias_inicio/maxDia*100).toFixed(2);
        const width = ((e.dias_fin-e.dias_inicio)/maxDia*100).toFixed(2);
        const diasTxt = `${{e.dias_inicio}}–${{e.dias_fin}} días`;
        const dSafe = (e.descripcion||'').replace(/'/g,"&#39;").replace(/"/g,"&quot;");
        const cSafe = (e.caracteristicas||'').replace(/'/g,"&#39;").replace(/"/g,"&quot;");
        return `<div class="feno-gantt-row">
            <div class="feno-gantt-label">${{e.etapa}}<small>${{diasTxt}}</small></div>
            <div class="feno-gantt-track">
                <div class="feno-gantt-bar ${{ecClass}}"
                     style="left:${{left}}%;width:${{width}}%"
                     data-etapa="${{e.etapa}}" data-desc="${{dSafe}}"
                     data-car="${{cSafe}}" data-dias="${{diasTxt}}"
                     onmouseenter="fenoShowTip(event,this)"
                     onmouseleave="fenoHideTip()"
                     onmousemove="fenoMoveTip(event)">
                    ${{parseFloat(width)>8?e.etapa:''}}
                </div>
            </div>
            <div class="feno-gantt-days">${{diasTxt}}</div>
        </div>`;
    }}).join('');
}}

// ── Tooltip ───────────────────────────────────────────────────────────────
const fenoTip = document.getElementById('fenoTooltip');
function fenoShowTip(e,el) {{
    document.getElementById('fttEtapa').textContent = el.dataset.etapa;
    document.getElementById('fttDesc').textContent  = el.dataset.desc || '—';
    document.getElementById('fttCar').textContent   = el.dataset.car  || '';
    document.getElementById('fttDias').textContent  = '⏱ ' + el.dataset.dias;
    fenoTip.classList.add('visible');
    fenoMoveTip(e);
}}
function fenoHideTip() {{ fenoTip.classList.remove('visible'); }}
function fenoMoveTip(e) {{
    fenoTip.style.left = Math.min(e.clientX+14, window.innerWidth-260)+'px';
    fenoTip.style.top  = Math.min(e.clientY-10, window.innerHeight-150)+'px';
}}

// ── Vista meses por estado ────────────────────────────────────────────────
function fenoRenderMeses(c) {{
    const estados = DATOS_FENO.calendario[c];
    document.getElementById('fenoEmptyMeses').style.display   = estados ? 'none' : 'flex';
    document.getElementById('fenoMesesContent').style.display = estados ? 'block' : 'none';
    if (!estados) return;

    document.getElementById('fenoMesesTitulo').textContent =
        `Siembra / Cosecha — ${{fenoCap(c)}} · ${{Object.keys(estados).length}} estados`;

    const mesesCols = FENO_MESES_ABR.map(m=>`<th>${{m}}</th>`).join('');
    let html = `<thead><tr><th class="estado-col">Estado</th>${{mesesCols}}</tr></thead><tbody>`;

    Object.entries(estados).sort((a,b)=>a[0].localeCompare(b[0])).forEach(([estado,d])=>{{
        const cells = FENO_MESES_ABR.map((_,i)=>{{
            const isL=d.meses_lluvia.includes(i), isS=d.meses_secas.includes(i);
            const isSi=d.mes_siembra.includes(i), isCo=d.mes_cosecha.includes(i);
            const capas=[];
            if(isL)  capas.push('lluvia');
            if(isS)  capas.push('secas');
            if(isSi) capas.push('siembra');
            if(isCo) capas.push('cosecha');
            if(!capas.length) return '<td class="feno-mes-td"></td>';
            if(capas.length===1) return `<td class="feno-mes-td feno-cell-${{capas[0]}}" title="${{capas[0]}}"></td>`;
            const chips=capas.map(cap=>`<div class="feno-chip feno-chip-${{cap}}"></div>`).join('');
            return `<td class="feno-mes-td" title="${{capas.join(', ')}}"><div class="feno-cell-chips">${{chips}}</div></td>`;
        }}).join('');
        html+=`<tr><td class="feno-estado-td">${{estado}}</td>${{cells}}</tr>`;
    }});

    html+='</tbody>';
    document.getElementById('fenoMesesTable').innerHTML=html;
}}

// ── Switch de vista interna ───────────────────────────────────────────────
function fenoSwitchView(vista, el) {{
    fenoVista=vista;
    document.querySelectorAll('.feno-view-tab').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.feno-view-panel').forEach(p=>p.classList.remove('active'));
    el.classList.add('active');
    document.getElementById(`feno-panel-${{vista}}`).classList.add('active');
    if(fenoCultivoActivo){{
        if(vista==='gantt') fenoRenderGantt(fenoCultivoActivo);
        else fenoRenderMeses(fenoCultivoActivo);
    }}
}}

// ══ UTIL ═══════════════════════════════════════════════════════════════════
function cap(s) {{ return s ? s.charAt(0).toUpperCase()+s.slice(1) : ''; }}
</script>
</body>
</html>"""

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Dashboard generado: {output}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("📂 Cargando datos...")
    enfermedades, calendario, exportacion, etapas = cargar_datos()
    print(f"   ✅ {len(enfermedades)} enfermedades | {len(calendario)} registros calendario | {len(etapas)} etapas fenológicas")

    print("🔄 Procesando datos mapa...")
    estados_mapa = construir_datos_mapa(calendario, enfermedades, exportacion)
    print(f"   ✅ {len(estados_mapa)} estados")

    print("🔄 Procesando datos enfermedades...")
    registros_enf = construir_datos_enfermedades(enfermedades)
    difs = sorted(set(r["dificultad"] for r in registros_enf))
    print(f"   ✅ {len(registros_enf)} registros | dificultades: {difs}")

    print("🔄 Procesando datos fenológicos...")
    datos_feno = construir_datos_fenologicos(calendario, etapas)
    print(f"   ✅ {len(datos_feno['calendario'])} cultivos calendario | {len(datos_feno['etapas'])} cultivos con etapas")

    print("🎨 Generando dashboard unificado...")
    generar_html(estados_mapa, registros_enf, datos_feno)
    print(f"\n✅ Listo. Abre {OUTPUT_HTML} en tu navegador.")

if __name__ == "__main__":
    main()