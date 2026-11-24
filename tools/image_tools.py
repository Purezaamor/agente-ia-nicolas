import os
import base64
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from config.settings import OPENAI_API_KEY
from services.document_service import create_vector_store

model_vision = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=OPENAI_API_KEY,
    max_tokens=3000,
)

@tool
def procesar_imagen_documento(ruta_imagen: str, nombre_archivo: str, categoria: str = "apuntes") -> str:
    """Lee una imagen (apunte de facultad, planilla manuscrita, boleta o mapa) y la indexa en la base de conocimiento."""
    if not os.path.exists(ruta_imagen):
        return f"Error: No se encontró la imagen en {ruta_imagen}"

    with open(ruta_imagen, "rb") as f:
        imagen_base64 = base64.b64encode(f.read()).decode("utf-8")

    mensaje = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Transcribí de forma LITERAL y COMPLETA todo el contenido de esta imagen "
                        "(apuntes de estudio, textos impresos, manuscritos, fórmulas, tablas o datos de campo). "
                        "No resumas, no omitas detalles y NO agregues información externa que no esté en la imagen. "
                        "Mantené títulos y estructura clara."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{imagen_base64}"},
                },
            ],
        }
    ]

    try:
        response = model_vision.invoke(mensaje)
        texto_extraido = response.content

        carpeta_destino = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "documentos",
            categoria.strip().lower(),
        )
        os.makedirs(carpeta_destino, exist_ok=True)

        archivo_txt = os.path.join(carpeta_destino, f"{nombre_archivo.strip()}.txt")
        with open(archivo_txt, "a", encoding="utf-8") as f:
            f.write(f"\n=== Documento: {nombre_archivo} ===\n{texto_extraido}\n")

        create_vector_store()

        return f"Imagen transcrita e indexada en '{categoria}/{nombre_archivo}.txt':\n\n{texto_extraido}"
    except Exception as e:
        return f"Error al procesar la imagen: {str(e)}"