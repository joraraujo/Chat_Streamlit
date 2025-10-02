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
modelo = "granite3.2-vision"

st.set_page_config(page_title="LLM local", page_icon="🤖")
st.title("💬 LLM Local com API Ollama")

# Sessão de estado para armazenar histórico
if "mensagens" not in st.session_state:
    st.session_state["mensagens"] = []

# Upload da imagem (opcional agora)
imagem_uploaded_file = st.file_uploader("Envie uma imagem (opcional)", type=["png", "jpg", "jpeg"])

# Campo de prompt
prompt = st.chat_input("Digite sua pergunta:")

if prompt:
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

        try:
            resposta = requests.post(url_api, json=dados, stream=True, timeout=240) # Mantenha stream=True

            if resposta.status_code == 200:
                # 1. Exibir a mensagem do usuário imediatamente
                with st.chat_message("user"):
                    st.markdown(f"**Você:**\n{prompt}", unsafe_allow_html=True)
                    if imagem_bytes_para_historico:
                        st.image(imagem_bytes_para_historico, width=300)

                # 2. Preparar para exibir a resposta do assistente em streaming
                full_assistant_response_content = "" # Acumula a resposta completa para o histórico

                with st.chat_message("assistant"):
                    # Definir um gerador que irá produzir chunks de texto
                    def generate_chunks():
                        nonlocal full_assistant_response_content # Permite modificar a variável externa
                        for linha in resposta.iter_lines():
                            if linha:
                                try:
                                    parte = json.loads(linha.decode('utf-8'))
                                    texto = parte.get("message", {}).get("content")
                                    if texto:
                                        full_assistant_response_content += texto # Acumula para o histórico
                                        yield texto # Envia para o Streamlit exibir
                                except json.JSONDecodeError:
                                    error_chunk = "[Erro ao decodificar parte da resposta]"
                                    full_assistant_response_content += error_chunk
                                    yield error_chunk
                    
                    # Usa st.write_stream para exibir os chunks do gerador
                    # st.write_stream retorna a string final acumulada
                    final_response_displayed = st.write_stream(generate_chunks())

                # 3. Adicionar a conversa completa ao histórico da sessão
                st.session_state["mensagens"].append({
                    "usuario": prompt,
                    "imagem": imagem_bytes_para_historico,  # Armazena os bytes da imagem
                    "resposta": final_response_displayed # A resposta completa obtida via streaming
                })

            else:
                st.error(f"Erro na requisição: {resposta.status_code}")
                st.text(resposta.text)
                # Adicionar apenas a mensagem do usuário e o erro ao histórico, se desejar
                st.session_state["mensagens"].append({
                    "usuario": prompt,
                    "imagem": imagem_bytes_para_historico,
                    "resposta": f"Erro na requisição: {resposta.status_code}\n{resposta.text}"
                })


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
