FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY secrets.json .

COPY sidecar.py .

CMD ["python", "sidecar.py"]