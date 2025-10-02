```bash
docker build -t chat_streamlit .
```

```bash
docker run -p 8501:8501 --name chat_streamlit-app chat_streamlit

```

```bash
sudo docker network connect ollama-network chat_streamlit-app
```

```bash
git fetch origin
git reset --hard origin/main
```

