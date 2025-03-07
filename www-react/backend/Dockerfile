# backend/Dockerfile
FROM python:3.9-slim

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your backend code
COPY . .

# Expose port 5000 for your Python app
EXPOSE 5000

# Run your app (adjust as needed)
CMD ["python", "app.py"]
