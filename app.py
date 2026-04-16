# app.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Sirve el Excel como archivo estático
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
@app.head("/")  # para solucionar el 405
async def index():
    html = open("agrocker-generador.html", encoding="utf-8").read()
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    html = html.replace(
        "const ANTHROPIC_API_KEY = window.__ENV__?.ANTHROPIC_API_KEY || '';",
        f"const ANTHROPIC_API_KEY = '{api_key}';"
    ).replace(
        "const EXCEL_URL      = window.__ENV__?.EXCEL_URL      || '';",
        f"const EXCEL_URL      = '/static/textos.xlsx';"
    )
    return HTMLResponse(content=html)

# @app.get("/")
# @app.head("/")
# async def index():
#     html = open("agrocker-generador.html", encoding="utf-8").read()
    
#     api_key  = os.getenv("ANTHROPIC_API_KEY", "")
#     excel_url = "/static/textos.xlsx"
    
#     # Inyecta las variables antes de servir el HTML
#     html = html.replace(
#         "const CLAUDE_API_KEY = window.__ENV__?.CLAUDE_API_KEY || '';",
#         f"const CLAUDE_API_KEY = '{api_key}';"
#     ).replace(
#         "const EXCEL_URL      = window.__ENV__?.EXCEL_URL      || '';",
#         f"const EXCEL_URL      = '{excel_url}';"
#     )
    
#     return HTMLResponse(content=html)