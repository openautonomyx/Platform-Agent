# Platform Agent - Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy Python files
COPY src/ /app/src/
COPY pyproject.toml /app/

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8080

# Run agent
CMD ["uv", "run", "python", "-m", "platform_agent"]