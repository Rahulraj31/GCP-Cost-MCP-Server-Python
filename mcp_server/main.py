import asyncio
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp_server.pricing.client import PricingClient
from mcp_server.freetier.service import FreeTierService
from mcp_server.utils.auth import get_authenticated_client
from mcp_server.models.billing import (
    EstimateCostOutput, 
    CostBreakdown
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gcp-cost-mcp")

# Initialize FastMCP
mcp = FastMCP("GCP Cost Estimator")

# Global services (managed lazily)
_client: Optional[PricingClient] = None
_free_tier_service = FreeTierService()

async def get_pricing_client() -> PricingClient:
    """Lazily initializes and returns the PricingClient."""
    global _client
    if _client is None:
        client = await get_authenticated_client()
        _client = PricingClient(client)
    return _client

@mcp.tool()
async def list_services(page_size: int = 50, page_token: Optional[str] = None):
    """
    Lists all publicly available Google Cloud services.
    Use this to find the service ID for a specific GCP product.
    """
    logger.info("Tool 'list_services' called")
    client = await get_pricing_client()
    return await client.list_services(page_size=page_size, page_token=page_token)

@mcp.tool()
async def list_skus(service_id: str, page_size: int = 50, page_token: Optional[str] = None):
    """
    Lists SKUs (Stock Keeping Units) for a specific GCP service.
    Use this to find the correct SKU ID for the instances/storage you want to estimate.
    """
    logger.info(f"Tool 'list_skus' called for service: {service_id}")
    client = await get_pricing_client()
    return await client.list_skus(service_id=service_id, page_size=page_size, page_token=page_token)

@mcp.tool()
async def get_sku_price(sku_id: str, service_id: str):
    """
    Gets detailed pricing information for a specific SKU.
    In v1, you must provide the service_id.
    """
    logger.info(f"Tool 'get_sku_price' called for SKU: {sku_id} in service: {service_id}")
    client = await get_pricing_client()
    sku = await client.get_sku_by_id(sku_id, service_id)
    if not sku:
        return {"error": f"SKU {sku_id} not found in service {service_id}"}
    return sku

@mcp.tool()
async def get_estimation_guide(service_name: str):
    """
    Provides a guide for what information is needed to estimate costs for any Google Cloud service.
    Call this FIRST to understand what details (region, specs, usage) you need from the user.
    """
    logger.info(f"Tool 'get_estimation_guide' called for service: {service_name}")
    client = await get_pricing_client()
    service_id, display_name = await client.find_service_by_name(service_name)
    
    free_tier_info = await _free_tier_service.get_free_tier(service_name)
    
    # Simple guide generation
    guide = {
        "service_name": display_name or service_name,
        "service_id": service_id,
        "parameters_needed": ["region", "usage_amount", "unit"],
        "free_tier": free_tier_info.model_dump() if free_tier_info else "No specific free tier info found.",
        "tip": "Start by finding the service, then list SKUs for that service ID."
    }
    return guide

@mcp.tool()
async def estimate_cost(
    sku_id: str, 
    service_id: str,
    usage_amount: float, 
    service_name: Optional[str] = None,
    region: Optional[str] = None,
    description: Optional[str] = None,
    currency_code: str = "USD"
):
    """
    Estimates the cost for a specific SKU based on usage amount, applying free tier deductions if possible.
    """
    logger.info(f"Tool 'estimate_cost' called for SKU: {sku_id}, service: {service_id}, usage: {usage_amount}")
    client = await get_pricing_client()
    
    # Get SKU
    sku = await client.get_sku_by_id(sku_id, service_id)
    if not sku or not sku.pricing_info:
        return {"error": f"No pricing data found for SKU {sku_id} in service {service_id}"}
    
    # Use the latest pricing info
    pricing_info = sku.pricing_info[0]
    expr = pricing_info.pricing_expression
    unit = expr.usage_unit
    
    # Free tier handling
    total_usage = usage_amount
    billable_usage = usage_amount
    free_tier_applied = 0.0
    free_tier_note = ""
    free_tier_url = ""
    
    if service_name:
        free_tier_info = await _free_tier_service.get_free_tier(service_name)
        if free_tier_info:
            # Simple matching logic for demonstration (matching units)
            for item in free_tier_info.items:
                if item.unit.lower() in unit.lower() or unit.lower() in item.unit.lower():
                    free_tier_applied = min(total_usage, item.amount)
                    billable_usage = max(0.0, total_usage - item.amount)
                    free_tier_note = f"Applied free tier: {item.amount} {item.unit}"
                    free_tier_url = free_tier_info.source_url
                    break

    # Calculate cost
    estimated_cost = client.calculate_cost(expr, billable_usage)
    
    price_per_unit = estimated_cost / billable_usage if billable_usage > 0 else 0.0
    
    breakdown = CostBreakdown(
        sku_id=sku_id,
        usage_amount=total_usage,
        unit=unit,
        estimated_cost=estimated_cost,
        currency_code=currency_code,
        price_per_unit=price_per_unit,
        tiered_pricing=len(expr.tiered_rates) > 1,
        number_of_tiers=len(expr.tiered_rates),
        service_name=service_name,
        region=region,
        description=description,
        total_usage=total_usage,
        free_tier_applied=free_tier_applied,
        billable_usage=billable_usage,
        free_tier_note=free_tier_note,
        free_tier_source_url=free_tier_url
    )
    
    return EstimateCostOutput(estimate=breakdown)

def main():
    """Main entry point for the MCP server, supporting both stdio and sse transports."""
    import sys
    import os
    
    # Support both transport modes: stdio (default) and sse
    # SSE is better for Cloud Run
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if len(sys.argv) > 1:
        if sys.argv[1] in ["sse", "stdio"]:
            transport = sys.argv[1]
    
    logger.info(f"Starting GCP Cost MCP Server with {transport} transport")
    
    if transport == "sse":
        import uvicorn
        # For SSE, we use uvicorn to host the sse_app
        # This allows us to explicitly set the port (defaulting to 8080 for Cloud Run)
        port = int(os.getenv("PORT", 8080))
        host = os.getenv("HOST", "127.0.0.1")
        uvicorn.run(mcp.sse_app(), host=host, port=port)
    else:
        # stdio transport (default)
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
