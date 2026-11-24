from services.document_service import create_vector_store

print("Indexando documentos...")
vs = create_vector_store()
if vs:
    print("Indexacion completada.")
else:
    print("No se encontraron documentos.")