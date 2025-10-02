import streamlit as st
import base64
import requests
import json
from io import BytesIO

# Função para converter imagem em base64
def converter_imagem_para_base64(uploaded_file):
    try:
        imagem_bytes = uploaded_file.read()
        uploaded_file.seek(0)
        return base64.b64encode(imagem_bytes).decode('utf-8')
    except Exception as e:
        st.error(f"Erro ao processar a imagem: {e}")
        return None

# Configurações iniciais
url_api = "http://ollama:11434/api/chat"
modelo = "granite4:micro-h"

st.set_page_config(page_title="LLM local", page_icon="🤖")
st.title("💬 LLM Local com API Ollama")

# Sessão de estado para armazenar histórico
if "mensagens" not in st.session_state:
    st.session_state["mensagens"] = []

# Upload da imagem (opcional agora)
imagem = st.file_uploader("Envie uma imagem (opcional)", type=["png", "jpg", "jpeg"])

# Campo de prompt
prompt = st.chat_input("Digite sua pergunta:")

if prompt:
    with st.spinner("Processando..."):

        dados = {
            "model": modelo,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        imagem_base64 = None
        if imagem:
            imagem_base64 = converter_imagem_para_base64(imagem)
            if imagem_base64:
                dados["messages"][0]["images"] = [imagem_base64]

        try:
            resposta = requests.post(url_api, json=dados, stream=True, timeout=240)

            if resposta.status_code == 200:
                resposta_completa = ""
                for linha in resposta.iter_lines():
                    if linha:
                        try:
                            parte = json.loads(linha.decode('utf-8'))
                            texto = parte.get("message", {}).get("content")
                            if texto:
                                resposta_completa += texto
                        except json.JSONDecodeError:
                            resposta_completa += "[Erro ao decodificar parte da resposta]"

                # Adiciona ao histórico
                st.session_state["mensagens"].append({
                    "usuario": prompt,
                    "imagem": imagem,  # Pode ser None
                    "resposta": resposta_completa
                })

            else:
                st.error(f"Erro na requisição: {resposta.status_code}")
                st.text(resposta.text)

        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao conectar à API: {e}")

# Exibir histórico
if st.session_state["mensagens"]:
    st.subheader("Histórico de Conversa")

    for msg in st.session_state["mensagens"]:
        with st.chat_message("user"):
            st.markdown(f"**Você:**\n{msg['usuario']}", unsafe_allow_html=True)
            if msg.get("imagem"):
                st.image(msg["imagem"], width=300)

        with st.chat_message("assistant"):
            st.markdown(f"**Assistente:**\n{msg['resposta']}", unsafe_allow_html=True)
