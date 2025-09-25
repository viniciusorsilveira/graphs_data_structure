FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential  \
    python3-dev 

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/output

CMD ["sh", "-c", "python extrai_dados.py && python grafo.py && cp *.csv *.html /app/output/ 2>/dev/null || true"]
