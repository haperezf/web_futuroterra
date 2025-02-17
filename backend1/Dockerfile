FROM python:3.9-slim

WORKDIR /app

# Copy the requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask app code
COPY . .

# Expose port 8000 for Flask
EXPOSE 8000

CMD ["python", "app.py"]
