from utils.supervisor import create_fieldview_supervisor

def main():
    print("=" * 50)
    print("AGENTE FIELDVIEW - INGENIERO AGRONOMO DIGITAL")
    print("=" * 50)
    print("Escribi tu consulta y apreta Enter.")
    print("Para salir escribi 'salir'.\n")

    app = create_fieldview_supervisor()

    while True:
        user_request = input(">>> ")

        if user_request.lower() in ("salir", "exit", "q"):
            print("Cerrando agente.")
            break

        if not user_request.strip():
            continue

        print("\nProcesando...\n")
        config = {"configurable": {"thread_id": "session_001"}}

        result = app.invoke(
            {"messages": [{"role": "user", "content": user_request}]},
            config=config,
        )

        print("=" * 50)
        for message in result["messages"]:
            if hasattr(message, "content") and message.content:
                print(f"\n{message.content}")
        print("\n" + "=" * 50)
        print("¿Otra consulta? (escribi 'salir' para terminar)\n")

if __name__ == "__main__":
    main()