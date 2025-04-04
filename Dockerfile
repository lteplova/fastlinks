FROM python:3.9

RUN mkdir /fastapi_app

WORKDIR /fastapi_app

COPY requirements.txt .

RUN  pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh

CMD uvicorn main:app --host 0.0.0.0 --port 8000
