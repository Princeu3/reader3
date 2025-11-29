FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY server.py reader3.py ./
COPY templates ./templates

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8080

# Run server
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
