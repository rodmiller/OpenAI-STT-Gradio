FROM python:3.8-slim

WORKDIR /usr/src/app

COPY . .
RUN pip install -r requirements.txt

RUN apt-get update
RUN apt-get install -y --no-install-recommends git
EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD ["python", "main.py"]