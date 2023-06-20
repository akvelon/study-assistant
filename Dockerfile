FROM python:3.11.3-slim
WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

ARG OPENAI_API_KEY
ARG HOST

ENV openai_key=$OPENAI_API_KEY
ENV host=$HOST

EXPOSE 8080
CMD ["/bin/bash", "-c", "python3 start.py"]
