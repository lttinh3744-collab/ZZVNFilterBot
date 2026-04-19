FROM python:3.12-slim

# Cài Chrome và các thư viện cần thiết
RUN apt-get update && apt-get install -y \
    wget gnupg2 unzip curl ca-certificates \
    libnss3 libgconf-2-4 libxi6 libxcomposite1 libxcursor1 \
    libxdamage1 libxrandr2 libxtst6 libasound2 libpangocairo-1.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libxss1 fonts-liberation xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Cài Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Tạo thư mục tạm cho Chrome
RUN mkdir -p /tmp/.com.google.Chrome && chmod -R 777 /tmp

CMD ["python", "bot.py"]
