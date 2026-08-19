FROM python:3.12-slim-bookworm

WORKDIR /app

COPY fast_api/ /app/
COPY models/vectorizer.pkl /app/models/vectorizer.pkl


RUN pip install -r requirements.txt

RUN python -m nltk.downloader stopwords wordnet

EXPOSE 8050

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8050", "--log-level", "info"]