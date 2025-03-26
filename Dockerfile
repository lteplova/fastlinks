FROM python:3.9

RUN mkdir /fastlinks:

WORKDIR /fastlinks

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

RUN chmod a+x docker/*.sh

# CMD ["python", "main.py"]
 # uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
# CMD uvicorn main:app --host 0.0.0.0 --port $PORT

CMD gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000
