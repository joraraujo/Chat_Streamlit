# Imagem base com Python
FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Copiar arquivos para o container
COPY . /app

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expor porta padrão do Streamlit
EXPOSE 8501

# Comando para rodar o Streamlit
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
