FROM selenium/standalone-chrome:latest

USER root

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Fix quyền cho thư mục
RUN mkdir -p /tmp/.com.google.Chrome && chmod -R 777 /tmp

USER seluser

CMD ["python3", "bot.py"]
