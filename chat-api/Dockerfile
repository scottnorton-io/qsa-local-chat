FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (minimal; no compilers left behind)
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps, including python-multipart for form handling
RUN pip install --no-cache-dir \
      fastapi \
      uvicorn[standard] \
      httpx \
      jinja2 \
      python-multipart \
      pypdf \
      python-docx

# Copy app code into the image
COPY . .

EXPOSE 8080

CMD ["uvicorn", "chat-api.main:app", "--host", "0.0.0.0", "--port", "8080"]
