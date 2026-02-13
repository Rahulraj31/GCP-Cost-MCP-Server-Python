import google.auth
from google.auth.transport.requests import Request
import httpx
import re
from httpx import AsyncClient

async def get_authenticated_client() -> AsyncClient:
    """
    Creates an authenticated httpx.AsyncClient using Google Application Default Credentials.
    """
    credentials, project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-billing.readonly"]
    )
    
    # Refresh credentials if necessary
    auth_req = Request()
    if not credentials.valid:
        credentials.refresh(auth_req)
        
    # Better approach for httpx: an auth class
    class GoogleAuth(httpx.Auth):
        def __init__(self, credentials):
            self.credentials = credentials

        def auth_flow(self, request):
            if not self.credentials.valid:
                self.credentials.refresh(Request())
            request.headers["Authorization"] = f"Bearer {self.credentials.token}"
            yield request

    return AsyncClient(auth=GoogleAuth(credentials), base_url="https://cloudbilling.googleapis.com")

def normalize_service_name(name: str) -> str:
    """Normalizes a service name for consistent lookups and caching."""
    # Remove common suffixes and normalize whitespace/case
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name)
    return name

SERVICE_ALIASES = {
    "gke": "kubernetes engine",
    "k8s": "kubernetes engine",
    "gcs": "cloud storage",
    "bq": "bigquery",
    "gcf": "cloud functions",
    "gae": "app engine",
    "gce": "compute engine",
    "cloud run functions": "cloud functions",
    "2nd gen functions": "cloud functions",
    "pubsub": "pub/sub",
    "cloud pubsub": "pub/sub",
}
