FROM python:3.11.7-bookworm
WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt /requirements.txt
COPY . .

RUN pip3 install -r /requirements.txt

FROM python:3.11.7-bookworm

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

WORKDIR /app

COPY --from=0 /opt/venv /opt/venv
COPY --from=0 /app ./

EXPOSE 50051

ENV PATH="/opt/venv/bin:$PATH"
CMD ["sh", "-c", "python -u grpc_server.py"]