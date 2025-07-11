FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:fastapi_app", "--host", "0.0.0.0", "--port", "3000", "--reload"]
