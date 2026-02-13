import httpx
from typing import List, Optional, Tuple
from ..models.billing import (
    ListServicesResponse, 
    ListSKUsResponse, 
    Service,
    SKU,
    PricingExpression
)
from ..utils.auth import get_authenticated_client, normalize_service_name, SERVICE_ALIASES

class PricingClient:
    """
    Client for interacting with the Google Cloud Billing Catalog API v1.
    """
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.base_url = "https://cloudbilling.googleapis.com"

    async def list_services(self, page_size: int = 5000, page_token: str = None) -> ListServicesResponse:
        """Lists all publicly available Google Cloud services."""
        params = {"pageSize": page_size}
        if page_token:
            params["pageToken"] = page_token
            
        response = await self.client.get("/v1/services", params=params)
        response.raise_for_status()
        return ListServicesResponse.model_validate(response.json())

    async def list_skus(self, service_id: str, page_size: int = 5000, page_token: str = None) -> ListSKUsResponse:
        """Lists SKUs for a specific service."""
        params = {"pageSize": page_size}
        if page_token:
            params["pageToken"] = page_token
            
        response = await self.client.get(f"/v1/services/{service_id}/skus", params=params)
        response.raise_for_status()
        return ListSKUsResponse.model_validate(response.json())

    async def get_sku_by_id(self, sku_id: str, service_id: str) -> Optional[SKU]:
        """Finds a specific SKU by its ID by listing SKUs for its service."""
        # Note: v1 doesn't have a direct GET /v1/skus/{id} for the catalog.
        # We list and find.
        resp = await self.list_skus(service_id)
        for sku in resp.skus:
            if sku.sku_id == sku_id:
                return sku
        return None

    async def find_service_by_name(self, service_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Searches for a GCP service by name and returns its (service_id, display_name).
        """
        normalized = normalize_service_name(service_name)
        search_term = SERVICE_ALIASES.get(normalized, normalized)
        
        resp = await self.list_services()
        
        # Try exact match
        for svc in resp.services:
            if svc.display_name.lower().strip() == search_term:
                return svc.service_id, svc.display_name
                
        # Try partial match
        for svc in resp.services:
            svc_name = svc.display_name.lower()
            if search_term in svc_name or svc_name in search_term:
                return svc.service_id, svc.display_name
                
        return None, None

    def calculate_cost(self, pricing_expression: PricingExpression, usage_amount: float) -> float:
        """
        Calculates the estimated cost based on usage amount and pricing tiered rates.
        """
        if not pricing_expression.tiered_rates:
            raise ValueError("No tiered rates available")

        # Sort tiers by start usage amount just in case
        tiers = sorted(pricing_expression.tiered_rates, key=lambda x: x.start_usage_amount)
        
        total_cost = 0.0
        remaining_usage = usage_amount

        for i, tier in enumerate(tiers):
            start_amount = tier.start_usage_amount
            
            if i + 1 < len(tiers):
                end_amount = tiers[i+1].start_usage_amount
            else:
                end_amount = remaining_usage + start_amount + 1 # Cover all remaining

            tier_range = end_amount - start_amount
            if tier_range <= 0:
                continue

            usage_in_tier = min(remaining_usage, tier_range)
            if usage_in_tier <= 0:
                continue
            
            # price_per_unit = units + nanos/1e9
            price_per_unit = float(tier.unit_price.units or 0) + (tier.unit_price.nanos / 1e9)
            
            # Apply display quantity normalization if needed (usually 1.0)
            total_cost += (usage_in_tier / (pricing_expression.display_quantity or 1.0)) * price_per_unit
            remaining_usage -= usage_in_tier

            if remaining_usage <= 0:
                break

        return total_cost
