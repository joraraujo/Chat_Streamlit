```bash docker build -t llm-streamlit .
docker run -p 8501:8501 --name Chat_Streamlit-app --network="host" llm-streamlit
```
