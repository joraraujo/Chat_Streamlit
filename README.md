docker build -t llm-streamlit .
docker run -p 8501:8501 --name llm-app --network="host" llm-streamlit