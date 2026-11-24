import streamlit as st
from utils.supervisor import create_fieldview_supervisor
import base64
import tempfile
import os

st.set_page_config(
    page_title="Agente de IA",
    page_icon="◈",
    layout="centered",
    menu_items=None,
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #000000; }
    .main .block-container { padding: 1.5rem 1rem 5rem 1rem; max-width: 720px; }
    section[data-testid="stSidebar"] { background: #000000; border-right: 1px solid #1A1A1A; }
    .header-wrapper { text-align: center; padding: 1.5rem 0 1rem 0; border-bottom: 1px solid #1A1A1A; margin-bottom: 1rem; }
    .header-icon { width: 44px; height: 44px; margin: 0 auto 12px auto; background: #FFFFFF; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
    h1 { font-size: 24px; font-weight: 600; color: #FFFFFF; text-align: center; letter-spacing: -0.3px; margin-bottom: 2px; }
    .subtitle { text-align: center; color: #999999; font-size: 13px; font-weight: 400; }
    .stChatMessage { background: transparent !important; border: none !important; padding: 4px 0 !important; }
    .stChatInput textarea { background: #0A0A0A; color: #F0F0F0; border: 1px solid #222222; border-radius: 14px; padding: 13px 18px; font-size: 14px; min-height: 50px; }
    .stChatInput textarea:focus { border-color: #444444; outline: none; }
    .stChatInput textarea::placeholder { color: #666666; }
    .stButton button { background: #0A0A0A; color: #CCCCCC; border: 1px solid #222222; border-radius: 12px; padding: 8px 18px; font-size: 12px; font-weight: 500; transition: all 0.2s; }
    .stButton button:hover { background: #111111; border-color: #444444; color: #FFFFFF; }
    .footer { position: fixed; bottom: 0; left: 0; right: 0; padding: 10px; text-align: center; background: #000000; border-top: 1px solid #141414; color: #666666; font-size: 10px; }
    ::-webkit-scrollbar { width: 0; }
    .stSpinner > div { border-color: #444444 transparent transparent transparent !important; }
    [data-testid="stToolbar"] { display: none; }
    .divider { border-top: 1px solid #1A1A1A; margin: 12px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-wrapper">
    <div class="header-icon">◈</div>
    <h1>Agente de IA</h1>
    <p class="subtitle">Diagnóstico y prescripción agrícola</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📋 Historial")
    if st.button("➕ Nuevo chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📷 Cargar imagen")
    uploaded_image = st.file_uploader("Foto de datos de campo", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    
    if uploaded_image:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded_image.read())
            ruta_temp = tmp.name
        campo = st.text_input("Nombre del campo", placeholder="Ej: LOTE-005")
        if st.button("Procesar imagen", use_container_width=True) and campo:
            with st.spinner("Leyendo imagen..."):
                from tools.image_tools import procesar_imagen_campo
                resultado = procesar_imagen_campo.invoke({"ruta_imagen": ruta_temp, "nombre_campo": campo})
                st.success("Procesada")
                st.text(resultado[:500])
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📁 Archivos cargados")
    docs_path = r"C:\fieldview_agent\documentos"
    if os.path.exists(docs_path):
        for root, dirs, files in os.walk(docs_path):
            for file in files:
                if file.endswith(".txt"):
                    st.markdown(f"• {file}")
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.caption("Ing. Nicolás Bruno · v1.0")

if "app" not in st.session_state:
    with st.spinner(""):
        st.session_state.app = create_fieldview_supervisor()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "session_001"

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Enviar mensaje..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(""):
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            result = st.session_state.app.invoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config=config,
            )
            output = ""
            for msg in reversed(result["messages"]):
                if hasattr(msg, "content") and msg.content and msg.type == "ai":
                    content = msg.content
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and "text" in item:
                                output = item["text"]
                                break
                    elif isinstance(content, str) and "transfer" not in content.lower():
                        output = content
                        break
            st.markdown(output or "Proceso completado.")

    st.session_state.messages.append({"role": "assistant", "content": output or "✓"})
    st.rerun()

st.markdown('<div class="footer">Agente de IA · Ing. Nicolás Bruno</div>', unsafe_allow_html=True)