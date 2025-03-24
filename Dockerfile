FROM python:3.9

RUN mkdir /fastlinks:

WORKDIR /fastlinks

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

RUN chmod a+x docker/*.sh

CMD ["python", "main.py"]
