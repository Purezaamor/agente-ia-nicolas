import os
from langchain.tools import tool
from services.document_service import get_vector_store, create_vector_store

@tool
def buscar_en_documentos(consulta: str) -> str:
    """Busca informacion en los archivos .txt cargados en la carpeta documentos."""
    vector_store = get_vector_store()
    if vector_store is None:
        vector_store = create_vector_store()
    if vector_store is None:
        return "No se encontraron archivos .txt en la carpeta 'documentos'."
    resultados = vector_store.similarity_search(consulta, k=5)
    if not resultados:
        return "No se encontro informacion relacionada en los documentos."
    respuesta = ""
    for i, doc in enumerate(resultados, 1):
        fuente = doc.metadata.get("source", "Desconocido")
        respuesta += f"\n--- {os.path.basename(fuente)} ---\n{doc.page_content}\n"
    return respuesta