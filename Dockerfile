FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose the API port
EXPOSE 4000

# Start the FastAPI server (Cloud API mode)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4000"]
