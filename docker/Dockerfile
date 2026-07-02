FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]