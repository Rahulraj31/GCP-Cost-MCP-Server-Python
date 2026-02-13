import httpx
from bs4 import BeautifulSoup
import re
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from .models import FreeTierInfo, FreeTierItem, FREE_TIER_PATTERNS

class FreeTierService:
    """
    Service for retrieving and extracting free tier info from GCP documentation.
    Includes a 24h cache to avoid excessive scraping.
    """
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = timedelta(hours=24)

    async def get_free_tier(self, service_name: str) -> Optional[FreeTierInfo]:
        """Retrieves free tier information for a service, using cache if available."""
        normalized_name = service_name.lower().strip()
        
        # Check cache
        if normalized_name in self.cache:
            entry = self.cache[normalized_name]
            if datetime.now() < entry["expires_at"]:
                return entry["info"]

        # Fetch from docs
        info = await self._fetch_from_docs(service_name)
        if info:
            self.cache[normalized_name] = {
                "info": info,
                "expires_at": datetime.now() + self.cache_ttl
            }
        return info

    async def _fetch_from_docs(self, service_name: str) -> Optional[FreeTierInfo]:
        """
        Implementation of the scraping and extraction logic.
        Uses a search query to find the pricing page and then scrapes it.
        """
        # In a real implementation, we'd use a search API or construct the URL.
        # For this port, we'll implement a robust extraction if given a URL or search results.
        # Here we'll simulate the workflow from the Go version.
        
        # 1. Search (Simplified: construct common pricing URL)
        url_slug = service_name.lower().replace(" ", "-")
        urls = [
            f"https://cloud.google.com/{url_slug}/pricing",
            f"https://cloud.google.com/pricing/details/{url_slug}"
        ]
        
        async with httpx.AsyncClient() as client:
            for url in urls:
                try:
                    resp = await client.get(url, follow_redirects=True)
                    if resp.status_code == 200:
                        return self._extract_from_html(resp.text, service_name, url)
                except Exception:
                    continue
        return None

    def _extract_from_html(self, html: str, service_name: str, url: str) -> Optional[FreeTierInfo]:
        """Extracts free tier items from HTML using BeautifulSoup and regex."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove noise
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
            
        text = soup.get_text(separator=' ')
        items = []
        
        for p in FREE_TIER_PATTERNS:
            matches = re.finditer(p["pattern"], text)
            for m in matches:
                try:
                    val_str = m.group(1).replace(",", "")
                    val = float(val_str)
                    items.append(FreeTierItem(
                        resource=p["resource"],
                        amount=val,
                        unit=p["unit"]
                    ))
                except ValueError:
                    continue
                    
        if not items:
            return None
            
        return FreeTierInfo(
            service_name=service_name,
            items=items,
            scope="account", # Defaulting as per Go version
            period="month",
            source_url=url
        )
