import streamlit as st
import base64
import requests
import json
from io import BytesIO

# Função para processar a imagem
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

# Configurações iniciais
url_api = "http://localhost:11434/chat"
url_models = "http://localhost:11434/api/tags"  # Retorna JSON com "models"

st.set_page_config(page_title="LLM local", page_icon="🤖")
st.title("💬 LLM Local com API Ollama")

# Obter lista de modelos disponíveis
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

# Se não encontrou nenhum modelo, definir um padrão
if not modelos_disponiveis:
    modelos_disponiveis = ["granite4:micro-h"]

# Seleção do modelo
modelo_selecionado = st.selectbox("Selecione o modelo", modelos_disponiveis)

# Sessão de estado para armazenar histórico
if "mensagens" not in st.session_state:
    st.session_state["mensagens"] = []

# Exibir histórico de mensagens
for msg in st.session_state["mensagens"]:
    role = msg["role"]
    with st.chat_message(role):
        st.markdown(msg["content"])
        if msg.get("imagem"):
            st.image(msg["imagem"], width=300)

# Upload da imagem (opcional)
imagem_uploaded_file = st.file_uploader("Envie uma imagem (opcional)", type=["png", "jpg", "jpeg"])

# Campo de prompt
prompt = st.chat_input("Digite sua pergunta:")

if prompt:
    # Processar imagem (se houver)
    imagem_bytes_para_historico, imagem_base64_para_api = processar_imagem_upload(imagem_uploaded_file)

    # Adiciona a mensagem do usuário ao histórico
    msg_usuario = {
        "role": "user",
        "content": prompt,
        "imagem": imagem_bytes_para_historico,
        "imagem_base64": imagem_base64_para_api
    }
    st.session_state["mensagens"].append(msg_usuario)

    # Exibe mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
        if imagem_bytes_para_historico:
            st.image(imagem_bytes_para_historico, width=300)

    with st.spinner("Processando..."):
        # Prepara dados para a API
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

        try:
            resposta = requests.post(url_api, json=dados, stream=True, timeout=240)

            if resposta.status_code == 200:
                # Exibir resposta do assistente em streaming
                full_response = ""
                with st.chat_message("assistant"):
                    for linha in resposta.iter_lines():
                        if linha:
                            try:
                                parte = json.loads(linha.decode('utf-8'))
                                texto = parte.get("message", {}).get("content")
                                if texto:
                                    st.write(texto)
                                    full_response += texto
                            except json.JSONDecodeError:
                                st.write("[Erro ao decodificar parte da resposta]")
                                full_response += "[Erro ao decodificar parte da resposta]"

                # Adiciona a resposta completa ao histórico
                st.session_state["mensagens"].append({
                    "role": "assistant",
                    "content": full_response
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
