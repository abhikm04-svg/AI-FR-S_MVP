FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

EXPOSE 8000

# The Windows ProactorEventLoop workaround in backend/api/__main__.py is a
# no-op on Linux -- plain uvicorn is fine here, no wrapper needed.
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
