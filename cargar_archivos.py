import os
from pypdf import PdfReader
from docx import Document
from pptx import Presentation
import pandas as pd
from services.document_service import create_vector_store

CARPETA_ENTRADA = "mis_archivos_entrada"
CARPETA_DESTINO = os.path.join("documentos", "apuntes")

os.makedirs(CARPETA_ENTRADA, exist_ok=True)
os.makedirs(CARPETA_DESTINO, exist_ok=True)

def extraer_texto(ruta, ext):
    if ext == ".pdf":
        reader = PdfReader(ruta)
        if reader.is_encrypted:
            reader.decrypt("")
        return "\n".join(p.extract_text() or "" for p in reader.pages)

    elif ext == ".docx":
        doc = Document(ruta)
        partes = [p.text for p in doc.paragraphs if p.text.strip()]
        for tabla in doc.tables:
            for fila in tabla.rows:
                partes.append(" | ".join(c.text.strip() for c in fila.cells))
        return "\n".join(partes)

    elif ext in [".xlsx", ".xls"]:
        hojas = pd.read_excel(ruta, sheet_name=None)
        partes = []
        for nombre_hoja, df in hojas.items():
            partes.append(f"--- Hoja: {nombre_hoja} ---")
            partes.append(df.fillna("").to_string(index=False))
        return "\n".join(partes)

    elif ext == ".pptx":
        prs = Presentation(ruta)
        partes = []
        for i, slide in enumerate(prs.slides, 1):
            textos_slide = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    textos_slide.append(shape.text_frame.text)
            if textos_slide:
                partes.append(f"--- Diapositiva {i} ---\n" + "\n".join(textos_slide))
        return "\n".join(partes)

    elif ext in [".txt", ".md"]:
        with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    return ""

def procesar_todo():
    archivos = os.listdir(CARPETA_ENTRADA)
    if not archivos:
        print(f"La carpeta '{CARPETA_ENTRADA}' está vacía.")
        return

    procesados = 0
    for archivo in archivos:
        ruta = os.path.join(CARPETA_ENTRADA, archivo)
        if not os.path.isfile(ruta):
            continue

        nombre_base, ext = os.path.splitext(archivo)
        ext = ext.lower()

        if ext not in [".pdf", ".docx", ".xlsx", ".xls", ".pptx", ".txt", ".md"]:
            continue

        ruta_txt = os.path.join(CARPETA_DESTINO, f"{nombre_base}.txt")
        if os.path.exists(ruta_txt):
            continue  # Ya fue procesado antes, lo saltea

        print(f"Extrayendo: {archivo}...")
        try:
            texto = extraer_texto(ruta, ext)
        except Exception as e:
            print(f"  [!] No se pudo leer '{archivo}': {e}")
            continue

        if len(texto.strip()) < 20:
            print(f"  [!] AVISO: '{archivo}' parece escaneado como imagen (sin texto seleccionable).")
            continue

        with open(ruta_txt, "w", encoding="utf-8") as f:
            f.write(f"=== Fuente: {archivo} ===\n\n{texto}")
        procesados += 1

    print("\nIndexando documentos en ChromaDB...")
    create_vector_store()
    print(f"¡Listo! Se agregaron {procesados} archivo(s) nuevos y quedó todo indexado.")

if __name__ == "__main__":
    procesar_todo()