import os
import io
import base64
import shutil
import tempfile
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader
from openai import OpenAI
from utils.supervisor import create_agro_supervisor
from tools.image_tools import procesar_imagen_documento
from tools.agro_db_tools import get_conn
from services.document_service import create_vector_store
from config.settings import OPENAI_API_KEY

app = FastAPI(title="Agente de IA")
app.mount("/static", StaticFiles(directory="static"), name="static")

supervisor_app = create_agro_supervisor()
openai_client = OpenAI(api_key=OPENAI_API_KEY)

@app.on_event("startup")
def inicializar_base_datos():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS establecimientos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) UNIQUE NOT NULL,
                renspa VARCHAR(100)
            );
            CREATE TABLE IF NOT EXISTS lotes (
                id SERIAL PRIMARY KEY,
                establecimiento_id INTEGER REFERENCES establecimientos(id) ON DELETE CASCADE,
                nombre_lote VARCHAR(100) NOT NULL,
                hectareas NUMERIC NOT NULL,
                cultivo_actual VARCHAR(100),
                campana VARCHAR(50),
                estado VARCHAR(50)
            );
            CREATE TABLE IF NOT EXISTS hacienda_movimientos (
                id SERIAL PRIMARY KEY,
                establecimiento VARCHAR(100) NOT NULL,
                fecha DATE DEFAULT CURRENT_DATE,
                tipo_movimiento VARCHAR(50) NOT NULL,
                categoria VARCHAR(100) NOT NULL,
                cantidad INTEGER NOT NULL,
                dte_numero VARCHAR(100),
                origen_destino VARCHAR(200),
                observaciones TEXT
            );
            CREATE TABLE IF NOT EXISTS contabilidad (
                id SERIAL PRIMARY KEY,
                fecha DATE DEFAULT CURRENT_DATE,
                tipo VARCHAR(20) NOT NULL,
                rubro VARCHAR(100) NOT NULL,
                descripcion TEXT,
                monto NUMERIC NOT NULL,
                moneda VARCHAR(10) DEFAULT 'ARS',
                establecimiento VARCHAR(100)
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Aviso de inicio de DB: {e}")

@app.get("/", response_class=HTMLResponse)
def servir_web():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/chat")
async def chat_con_agente(
    mensaje: str = Form(""),
    thread_id: str = Form("sesion_principal"),
    imagen: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
):
    config = {"configurable": {"thread_id": thread_id}}
    texto_final = mensaje.strip()

    if audio and audio.filename:
        ext = os.path.splitext(audio.filename)[1] or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            shutil.copyfileobj(audio.file, tmp)
            ruta_audio = tmp.name
        try:
            with open(ruta_audio, "rb") as f_aud:
                transcripcion = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f_aud,
                    language="es"
                )
            texto_audio = transcripcion.text.strip()
            texto_final = f"{texto_final}\n[Audio adjunto]: {texto_audio}".strip() if texto_final else texto_audio
        finally:
            if os.path.exists(ruta_audio):
                os.remove(ruta_audio)

    if imagen and imagen.filename:
        contenido_archivo = await imagen.read()
        nombre_lower = imagen.filename.lower()

        if nombre_lower.endswith(".pdf") or imagen.content_type == "application/pdf":
            reader = PdfReader(io.BytesIO(contenido_archivo))
            if reader.is_encrypted:
                reader.decrypt("")
            texto_pdf = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
            prompt_texto = texto_final or "Analizá este comprobante PDF y registralo donde corresponda."
            payload_usuario = f"{prompt_texto}\n\n--- Contenido del PDF ({imagen.filename}) ---\n{texto_pdf}"
        else:
            b64_img = base64.b64encode(contenido_archivo).decode("utf-8")
            mime = imagen.content_type or "image/jpeg"
            prompt_texto = texto_final or "Analizá esta imagen y extraé todos los datos relevantes. Si corresponde a lotes, hacienda o gastos/ingresos, registralo."
            payload_usuario = [
                {"type": "text", "text": prompt_texto},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64_img}"}},
            ]
    else:
        if not texto_final:
            return {"respuesta": "Escribí un mensaje o adjuntá una imagen, PDF o audio."}
        payload_usuario = texto_final

    result = supervisor_app.invoke(
        {"messages": [{"role": "user", "content": payload_usuario}]},
        config=config,
    )

    output = ""
    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content and not getattr(msg, "tool_calls", None):
            if isinstance(msg.content, str):
                output = msg.content
                break
            elif isinstance(msg.content, list):
                textos = [item["text"] for item in msg.content if isinstance(item, dict) and "text" in item]
                if textos:
                    output = "\n".join(textos)
                    break

    return {
        "respuesta": output or "No pude generar una respuesta.",
        "texto_interpretado": texto_final
    }

@app.post("/api/subir-documentos")
async def subir_documentos(
    archivos: List[UploadFile] = File(...),
    nombre_base: str = Form(...),
    categoria: str = Form("apuntes"),
):
    carpeta_destino = os.path.join("documentos", categoria.strip().lower())
    os.makedirs(carpeta_destino, exist_ok=True)
    archivo_txt = os.path.join(carpeta_destino, f"{nombre_base.strip()}.txt")

    procesados = 0
    for archivo in archivos:
        ext = os.path.splitext(archivo.filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            shutil.copyfileobj(archivo.file, tmp)
            ruta_temp = tmp.name

        try:
            if ext == ".pdf":
                reader = PdfReader(ruta_temp)
                texto_pdf = "\n".join(page.extract_text() or "" for page in reader.pages)
                with open(archivo_txt, "a", encoding="utf-8") as f:
                    f.write(f"\n=== PDF: {archivo.filename} ===\n{texto_pdf}\n")
                procesados += 1
            elif ext in [".txt", ".md"]:
                with open(ruta_temp, "r", encoding="utf-8", errors="ignore") as f_in:
                    texto = f_in.read()
                with open(archivo_txt, "a", encoding="utf-8") as f_out:
                    f_out.write(f"\n=== Archivo: {archivo.filename} ===\n{texto}\n")
                procesados += 1
            else:
                procesar_imagen_documento.invoke({
                    "ruta_imagen": ruta_temp,
                    "nombre_archivo": nombre_base.strip(),
                    "categoria": categoria,
                })
                procesados += 1
        finally:
            if os.path.exists(ruta_temp):
                os.remove(ruta_temp)

    create_vector_store()
    return {"ok": True, "cantidad": procesados}

@app.get("/api/dashboard")
def obtener_datos_panel():
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT COALESCE(SUM(CASE WHEN tipo_movimiento IN ('INGRESO', 'NACIMIENTO') THEN cantidad ELSE -cantidad END), 0) AS total_cabezas
            FROM hacienda_movimientos;
        """)
        cabezas = cur.fetchone()["total_cabezas"]

        cur.execute("""
            SELECT moneda,
                   COALESCE(SUM(CASE WHEN tipo = 'INGRESO' THEN monto ELSE -monto END), 0) AS saldo
            FROM contabilidad
            GROUP BY moneda;
        """)
        saldos = {r["moneda"]: float(r["saldo"]) for r in cur.fetchall()}

        cur.execute("SELECT COUNT(*) AS cant_lotes, COALESCE(SUM(hectareas), 0) AS total_ha FROM lotes;")
        lotes_info = cur.fetchone()

        cur.close()
        conn.close()
        return {
            "cabezas": int(cabezas),
            "saldos": saldos,
            "lotes": int(lotes_info["cant_lotes"]),
            "hectareas": float(lotes_info["total_ha"]),
        }
    except Exception as e:
        return {"error": str(e), "cabezas": 0, "saldos": {}, "lotes": 0, "hectareas": 0}

@app.get("/api/tablas")
def obtener_tablas_detalle():
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT e.nombre AS campo, l.nombre_lote AS lote, l.hectareas, l.cultivo_actual
            FROM lotes l
            JOIN establecimientos e ON l.establecimiento_id = e.id
            ORDER BY e.nombre, l.nombre_lote;
        """)
        lotes = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT TO_CHAR(fecha, 'DD/MM/YYYY') AS fecha, establecimiento AS campo,
                   tipo_movimiento, categoria, cantidad, dte_numero AS numero_dte
            FROM hacienda_movimientos
            ORDER BY fecha DESC, id DESC LIMIT 30;
        """)
        hacienda = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT TO_CHAR(fecha, 'DD/MM/YYYY') AS fecha, tipo, rubro,
                   descripcion, moneda, monto
            FROM contabilidad
            ORDER BY fecha DESC, id DESC LIMIT 30;
        """)
        contabilidad = [dict(r) for r in cur.fetchall()]

        cur.close()
        conn.close()
        return {"lotes": lotes, "hacienda": hacienda, "contabilidad": contabilidad}
    except Exception as e:
        return {"error": str(e), "lotes": [], "hacienda": [], "contabilidad": []}

@app.get("/api/documentos")
def listar_documentos():
    docs = []
    if os.path.exists("documentos"):
        for root, _, files in os.walk("documentos"):
            cat = os.path.basename(root)
            for f in sorted(files):
                if f.endswith(".txt"):
                    docs.append({"categoria": cat, "nombre": f.replace(".txt", "")})
    return {"documentos": docs}