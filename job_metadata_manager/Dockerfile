FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y vim

COPY . /app/

EXPOSE 5000

CMD ["python", "job_metadata_manager.py"]

