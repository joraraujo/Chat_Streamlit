#!/bin/bash

# Nome do container e da imagem
CONTAINER_NAME="chat_streamlit-app"
IMAGE_NAME="chat_streamlit"
NETWORK_NAME="ollama-network"

echo "=== Parando e removendo container antigo ==="
docker stop $CONTAINER_NAME 2>/dev/null
docker rm $CONTAINER_NAME 2>/dev/null

echo "=== Removendo imagem antiga ==="
docker rmi $IMAGE_NAME 2>/dev/null

echo "=== Atualizando código do repositório ==="
git fetch origin
git reset --hard origin/main

echo "=== Construindo nova imagem Docker ==="
docker build -t $IMAGE_NAME .

echo "=== Rodando container em background ==="
docker run -d -p 8501:8501 --name $CONTAINER_NAME $IMAGE_NAME

echo "=== Conectando container à rede do Ollama ==="
docker network connect $NETWORK_NAME $CONTAINER_NAME

echo "=== Atualização concluída! Acesse: http://localhost:8501 ==="
