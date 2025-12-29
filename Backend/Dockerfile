FROM python:3.10
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run sets PORT environment variable
ENV PORT=8080
EXPOSE 8080

# Use PORT from environment variable
CMD python server.py config.prd.ini