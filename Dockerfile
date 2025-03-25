FROM python:3.9

RUN mkdir /fastlinks:

WORKDIR /fastlinks

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
