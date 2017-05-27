FROM python:3.6

RUN mkdir /app
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt
CMD ["gunicorn", "-w", "10", "-b", "0.0.0.0:5000", "app.app_runner:app"]

ENV PYTHONPATH=/app
EXPOSE 5000
