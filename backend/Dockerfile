FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
# Install gunicorn for production server
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

# Create directory for keys if it doesn't exist
RUN mkdir -p /app/keys

EXPOSE 5000

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
