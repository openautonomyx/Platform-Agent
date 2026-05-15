# Platform Agent API - Dockerfile

FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir surrealdb aiohttp fastapi uvicorn

# Copy source
COPY src/ ./src/
COPY pyproject.toml ./

# Install package
RUN pip install -e .

# Expose
EXPOSE 3000

# Run
CMD ["uvicorn", "platform_agent.server:app", "--host", "0.0.0.0", "--port", "3000"]