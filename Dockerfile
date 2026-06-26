FROM python:3.13-slim

WORKDIR /app

# Install system deps if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# HF Spaces runs on port 7860 by default, but we expose 8503 as well
EXPOSE 7860 8503

# Run Streamlit on HF Spaces-compatible port
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
