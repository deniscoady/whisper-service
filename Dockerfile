FROM pytorch/pytorch:2.4.1-cuda12.4-cudnn9-runtime

RUN apt-get -y update && apt-get -y install

RUN apt-get -y install git ffmpeg libcudnn8 libcudnn8-dev

RUN mkdir -p /app/results

COPY src/* /app/

RUN pip3 install -r /app/requirements.txt

EXPOSE 8000
EXPOSE 8001
ENTRYPOINT [ "/usr/bin/bash", "/app/start-all.sh" ]