FROM python:3.9-slim

WORKDIR /app

COPY . /app

COPY botdb /data/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
