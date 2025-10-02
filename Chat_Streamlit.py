import streamlit as st
import base64
import requests
import json
from io import BytesIO

# Função para processar a imagem (leitura e conversão para base64)
def processar_imagem_upload(uploaded_file):
    if uploaded_file is None:
        return None, None # Retorna bytes e base64 como None
    try:
        imagem_bytes = uploaded_file.read() # Lê os bytes da imagem uma única vez
        imagem_base64 = base64.b64encode(imagem_bytes).decode('utf-8')
        return imagem_bytes, imagem_base64 # Retorna ambos
    except Exception as e:
        st.error(f"Erro ao processar a imagem: {e}")
        return None, None

# Configurações iniciais
url_api = "http://ollama:11434/api/chat"
modelo = "granite4:micro-h"

st.set_page_config(page_title="LLM local", page_icon="🤖")
st.title("💬 LLM Local com API Ollama")

# Sessão de estado para armazenar histórico
if "mensagens" not in st.session_state:
    st.session_state["mensagens"] = []

# Exibir histórico de mensagens no início
for msg in st.session_state["mensagens"]:
    role = msg["role"]
    with st.chat_message(role):
        st.markdown(msg["content"])
        if "imagem" in msg and msg["imagem"] is not None:
            st.image(msg["imagem"], width=300)

# Upload da imagem (opcional agora)
imagem_uploaded_file = st.file_uploader("Envie uma imagem (opcional)", type=["png", "jpg", "jpeg"])

# Campo de prompt
prompt = st.chat_input("Digite sua pergunta:")

if prompt:
    # Adiciona a mensagem do usuário ao histórico e a exibe
    st.session_state.mensagens.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Processando..."):
        # Prepara os dados para a API
        dados = {
            "model": modelo,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        # Variáveis para armazenar a imagem para a API e para o histórico
        imagem_bytes_para_historico = None
        imagem_base64_para_api = None

        if imagem_uploaded_file:
            # Processa a imagem: obtém os bytes e a versão base64
            imagem_bytes_para_historico, imagem_base64_para_api = processar_imagem_upload(imagem_uploaded_file)
            if imagem_base64_para_api:
                dados["messages"][0]["images"] = [imagem_base64_para_api]
            # Adiciona a imagem à última mensagem do usuário no histórico
            if imagem_bytes_para_historico:
                st.session_state.mensagens[-1]["imagem"] = imagem_bytes_para_historico
                with st.chat_message("user"): # Re-exibe a imagem sob a mensagem do usuário
                     st.image(imagem_bytes_para_historico, width=300)


        try:
            resposta = requests.post(url_api, json=dados, stream=True, timeout=240)

            if resposta.status_code == 200:
                # Exibe a resposta do assistente em streaming
                with st.chat_message("assistant"):
                    def generate_chunks():
                        for linha in resposta.iter_lines():
                            if linha:
                                try:
                                    parte = json.loads(linha.decode('utf-8'))
                                    texto = parte.get("message", {}).get("content")
                                    if texto:
                                        yield texto
                                except json.JSONDecodeError:
                                    yield "[Erro ao decodificar parte da resposta]"
                    
                    # Usa st.write_stream para exibir e capturar a resposta completa
                    full_response = st.write_stream(generate_chunks())
                
                # Adiciona a resposta completa do assistente ao histórico
                st.session_state.mensagens.append({"role": "assistant", "content": full_response})

            else:
                st.error(f"Erro na requisição: {resposta.status_code}")
                st.text(resposta.text)
                error_message = f"Erro na requisição: {resposta.status_code}\n{resposta.text}"
                st.session_state.mensagens.append({"role": "assistant", "content": error_message})

        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao conectar à API: {e}")
            error_message = f"Erro ao conectar à API: {e}"
            st.session_state.mensagens.append({"role": "assistant", "content": error_message})
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao conectar à API: {e}")
            # Adicionar apenas a mensagem do usuário e o erro ao histórico
            st.session_state["mensagens"].append({
                "usuario": prompt,
                "imagem": imagem_bytes_para_historico,
                "resposta": f"Erro ao conectar à API: {e}"
            })

# Exibir histórico
if st.session_state["mensagens"]:
    st.subheader("Histórico de Conversa")

    for msg in st.session_state["mensagens"]:
        with st.chat_message("user"):
            st.markdown(f"**Você:**\n{msg['usuario']}", unsafe_allow_html=True)
            if msg.get("imagem"): # Verifica se existem bytes da imagem
                st.image(msg["imagem"], width=300) # st.image pode renderizar bytes diretamente

        with st.chat_message("assistant"):
            st.markdown(f"**Assistente:**\n{msg['resposta']}", unsafe_allow_html=True)
