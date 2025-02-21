FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for cairosvg
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    libpango1.0-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"] 