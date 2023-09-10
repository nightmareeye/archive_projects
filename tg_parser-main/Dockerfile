FROM python:3.10

COPY requirements.txt /requirements.txt

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY data /code/data

COPY src /code/src

WORKDIR /code/src

ENTRYPOINT ["python", "-m", "main"]
