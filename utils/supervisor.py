from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
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

def create_agro_supervisor():
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)
    memory = MemorySaver()

    tools = [
        buscar_en_documentos,
        registrar_campo_o_lote,
        consultar_campos_y_lotes,
        registrar_movimiento_hacienda,
        consultar_stock_hacienda,
        registrar_movimiento_contable,
        consultar_resumen_contable,
    ]

    prompt = (
        "Sos el asistente central de gestión agropecuaria, contable y de apuntes de estudio.\n"
        "REGLAS OBLIGATORIAS:\n"
        "1. Si el usuario pregunta sobre cualquier tema técnico, agrícola, ganadero, legal, estadístico o de estudio "
        "(por ejemplo: curado de semillas, fungicidas, pasturas, parición, sanidad, etc.), "
        "SIEMPRE ejecutá PRIMERO la herramienta 'buscar_en_documentos' con palabras clave relevantes antes de responder.\n"
        "2. Respondé ÚNICAMENTE con los datos obtenidos de tus herramientas o de los documentos encontrados. "
        "PROHIBIDO inventar, suponer o usar conocimiento externo que no esté en los documentos o en la base de datos.\n"
        "3. Si después de buscar en los documentos no aparece información sobre ese tema, decí literalmente: "
        "'No encontré información sobre ese tema en tus documentos cargados.'\n"
        "4. Nunca digas que vas a derivar a otro especialista: vos mismo ejecutás las herramientas y das la respuesta completa en español."
    )

    return create_react_agent(
        model=model,
        tools=tools,
        prompt=prompt,
        checkpointer=memory,
    )