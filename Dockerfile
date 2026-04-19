FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium --with-deps

COPY . .
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
CMD ["python3", "app.py"]
