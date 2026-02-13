# GCP Cost MCP Server (Python)

An MCP server that enables AI assistants to estimate Google Cloud costs, powered by Cloud Billing Catalog API and built with Python.

Inspired from https://github.com/nozomi-koborinai/gcp-cost-mcp-server who built this is GoLang

## Description
This project is a Python port of the [gcp-cost-mcp-server](https://github.com/nozomi-koborinai/gcp-cost-mcp-server). It provides tools to interact with Google Cloud's pricing data and estimate costs, including automatic free tier deductions.

## Project Structure
- `mcp_server/`: Core application logic.
    - `pricing/`: Google Cloud Billing API client.
    - `freetier/`: Free tier information retrieval and scraping.
    - `models/`: Data structures and Pydantic models.
    - `utils/`: Common utilities and auth helpers.
- `tests/`: Unit and integration tests.

## Setup
1. Install `uv` if you haven't already.
2. Clone this repository.
3. Run `uv sync` to install dependencies.
4. Set up Application Default Credentials:
   ```bash
   gcloud auth application-default login
   ```

## Usage
Run the MCP server (stdio by default):
```bash
uv run python -m mcp_server.main
```

Run in SSE mode (for Cloud Run):
```bash
uv run python -m mcp_server.main sse
```
