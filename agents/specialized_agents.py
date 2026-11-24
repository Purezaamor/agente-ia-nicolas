from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tools.document_tools import buscar_en_documentos
from tools.agro_db_tools import (
    registrar_campo_o_lote,
    consultar_campos_y_lotes,
    registrar_movimiento_hacienda,
    consultar_stock_hacienda,
    registrar_movimiento_contable,
    consultar_resumen_contable,
)
from config.settings import OPENAI_API_KEY

model = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)

REGLA_CERO_INVENCION = (
    "REGLA ESTRICTA: Respondé ÚNICAMENTE con los datos obtenidos de tus herramientas o documentos. "
    "PROHIBIDO inventar, suponer o completar datos faltantes. Si algo no está registrado, decí literalmente: "
    "'No tengo esa información registrada'. Respondé siempre en español, claro y directo."
)

def create_campo_docs_agent():
    return create_react_agent(
        model=model,
        tools=[buscar_en_documentos, registrar_campo_o_lote, consultar_campos_y_lotes],
        name="especialista_campo_y_apuntes",
        prompt=(
            "Sos un especialista en gestión de campos, lotes y documentación técnica/apuntes de estudio. "
            "Usás 'buscar_en_documentos' para responder sobre apuntes, PDFs o imágenes cargadas, "
            "y 'registrar_campo_o_lote' / 'consultar_campos_y_lotes' para gestionar establecimientos y lotes. "
            + REGLA_CERO_INVENCION
        ),
    )

def create_hacienda_agent():
    return create_react_agent(
        model=model,
        tools=[registrar_movimiento_hacienda, consultar_stock_hacienda],
        name="especialista_hacienda",
        prompt=(
            "Sos el encargado de hacienda ganadera. Registrás ingresos, egresos, nacimientos y mortandad, "
            "y consultás el stock exacto por establecimiento y categoría. "
            "Si falta algún dato obligatorio para registrar (establecimiento, categoría o cantidad), pedilo antes de guardar. "
            + REGLA_CERO_INVENCION
        ),
    )

def create_contable_agent():
    return create_react_agent(
        model=model,
        tools=[registrar_movimiento_contable, consultar_resumen_contable],
        name="especialista_contable",
        prompt=(
            "Sos el asistente contable agropecuario. Registrás ingresos y egresos con su rubro, monto y moneda (ARS o USD), "
            "y calculás balances y resúmenes. Si el usuario no aclara si es ingreso o egreso, o falta el monto, pedilo antes de guardar. "
            + REGLA_CERO_INVENCION
        ),
    )