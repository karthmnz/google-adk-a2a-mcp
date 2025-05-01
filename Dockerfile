FROM python:3.11.11

WORKDIR /

COPY /app ./app
COPY /web ./web
COPY /mcp ./mcp
COPY pip.conf /etc/pip.conf
COPY entrypoint.py .
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
ENTRYPOINT [ "python3", "entrypoint.py"]