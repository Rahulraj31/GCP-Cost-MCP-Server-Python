# Use a slim Python image
FROM python:3.11-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN uv sync --frozen

# Expose port (if using SSE, MCP stdio doesn't need it but Cloud Run does for health checks)
EXPOSE 8080

# Environment variables
ENV PYTHONUNBUFFERED=1

# Run the MCP server in SSE mode for Cloud Run
CMD ["uv", "run", "gcp-cost-mcp", "sse"]
