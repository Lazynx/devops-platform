FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

COPY . .

CMD ["uv", "run", "uvicorn", "deployment_service.app:get_app", "--host", "0.0.0.0", "--port", "8002"]
