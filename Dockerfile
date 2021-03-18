FROM alpine:latest

RUN apk add --no-cache python3-dev cmd:pip3 \
    && pip3 install --upgrade pip

COPY main.py app/app.py
COPY requirements.txt app/requirements.txt
COPY helper.py app/helper.py

WORKDIR /app



RUN pip3 --no-cache-dir install -r requirements.txt

ENTRYPOINT [ "python3" ]

CMD [ "app.py" ]

# install mongodb
# buat persistance volume
# run main.py
# expose appropriate port

# refer
# 1. https://www.youtube.com/watch?v=GVs26OxzE3o - Docker Tutorial - basic setup a Python Flask Application in a Docker container
# 2. https://www.youtube.com/watch?v=uklyCSKQ1Po - MongoDB inside Docker Container
# 3. https://www.youtube.com/watch?v=prlixoDIfrc - Convert Python Flask APP to Docker Container | Docker | Python Flask
