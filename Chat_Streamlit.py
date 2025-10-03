import streamlit as st
import base64
import requests
import json

# -----------------------
# Função para processar a imagem
# -----------------------
def processar_imagem_upload(uploaded_file):
    if uploaded_file is None:
        return None, None
    try:
        imagem_bytes = uploaded_file.read()
        uploaded_file.seek(0)
        imagem_base64 = base64.b64encode(imagem_bytes).decode('utf-8')
        return imagem_bytes, imagem_base64
    except Exception as e:
        st.error(f"Erro ao processar a imagem: {e}")
        return None, None

# -----------------------
# Configurações iniciais
# -----------------------
ollama_host = "ollama"  # nome do container Ollama
url_api = f"http://ollama:11434/api/chat"
url_models = f"http://ollama:11434/api/models"

st.set_page_config(page_title="LLM Local", page_icon="🤖")
st.title("💬 LLM Local com API Ollama")

# -----------------------
# Listar modelos disponíveis
# -----------------------
try:
    resposta_modelos = requests.get(url_models, timeout=10)
    if resposta_modelos.status_code == 200:
        json_modelos = resposta_modelos.json()
        modelos_disponiveis = [m["name"] for m in json_modelos.get("models", [])]
    else:
        st.error(f"Erro ao obter modelos: {resposta_modelos.status_code}")
        modelos_disponiveis = []
except requests.exceptions.RequestException as e:
    st.error(f"Erro ao conectar à API de modelos: {e}")
    modelos_disponiveis = []

if not modelos_disponiveis:
    modelos_disponiveis = ["granite4:micro-h"]

modelo_selecionado = st.selectbox("Selecione o modelo", modelos_disponiveis)

# -----------------------
# Histórico de mensagens
# -----------------------
if "mensagens" not in st.session_state:
    st.session_state["mensagens"] = []

# Exibir histórico
for msg in st.session_state["mensagens"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("imagem"):
            st.image(msg["imagem"], width=300)

# -----------------------
# Upload de imagem opcional
# -----------------------
imagem_uploaded_file = st.file_uploader("Envie uma imagem (opcional)", type=["png", "jpg", "jpeg"])

# -----------------------
# Campo de prompt
# -----------------------
prompt = st.chat_input("Digite sua pergunta:")

if prompt:
    # Processar imagem
    imagem_bytes, imagem_base64 = processar_imagem_upload(imagem_uploaded_file)

    # Adicionar mensagem do usuário ao histórico
    msg_usuario = {
        "role": "user",
        "content": prompt,
        "imagem": imagem_bytes,
        "imagem_base64": imagem_base64
    }
    st.session_state["mensagens"].append(msg_usuario)

    # Exibir mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
        if imagem_bytes:
            st.image(imagem_bytes, width=300)

    # -----------------------
    # Preparar dados para API
    # -----------------------
    api_messages = []
    for msg in st.session_state["mensagens"]:
        api_msg = {"role": msg["role"], "content": msg["content"]}
        if msg.get("imagem_base64"):
            api_msg["images"] = [msg["imagem_base64"]]
        api_messages.append(api_msg)

    dados = {
        "model": modelo_selecionado,
        "messages": api_messages
    }

    # -----------------------
    # Chamada à API Ollama com streaming
    # -----------------------
    try:
        resposta = requests.post(url_api, json=dados, stream=True, timeout=300)

        if resposta.status_code == 200:
            with st.chat_message("assistant"):
                resposta_container = st.empty()
                texto_completo = ""

                for linha in resposta.iter_lines():
                    if linha:
                        try:
                            parte = json.loads(linha.decode("utf-8"))
                            texto_parte = parte.get("message", {}).get("content", "")
                            if texto_parte:
                                texto_completo += texto_parte
                                resposta_container.markdown(texto_completo)
                        except json.JSONDecodeError:
                            pass  # ignora chunks inválidos

            # Adiciona resposta completa ao histórico
            st.session_state["mensagens"].append({
                "role": "assistant",
                "content": texto_completo
            })
        else:
            error_message = f"Erro na requisição: {resposta.status_code}\n{resposta.text}"
            st.error(error_message)
            st.session_state["mensagens"].append({
                "role": "assistant",
                "content": error_message
            })

    except requests.exceptions.RequestException as e:
        error_message = f"Erro ao conectar à API: {e}"
        st.error(error_message)
        st.session_state["mensagens"].append({
            "role": "assistant",
            "content": error_message
        })
