FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
RUN mkdir -p /app/static
EXPOSE ${PORT:-8000}
ENV BACKEND_MODE=mock
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
