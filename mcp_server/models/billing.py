from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Money(BaseModel):
    model_config = {"populate_by_name": True}
    currency_code: str = Field(..., alias="currencyCode")
    units: Optional[str] = "0"
    nanos: Optional[int] = 0

class TieredRate(BaseModel):
    model_config = {"populate_by_name": True}
    start_usage_amount: float = Field(..., alias="startUsageAmount")
    unit_price: Money = Field(..., alias="unitPrice")

class AggregationInfo(BaseModel):
    model_config = {"populate_by_name": True}
    aggregation_level: Optional[str] = Field(None, alias="aggregationLevel")
    aggregation_interval: Optional[str] = Field(None, alias="aggregationInterval")
    aggregation_count: Optional[int] = Field(None, alias="aggregationCount")

class PricingExpression(BaseModel):
    model_config = {"populate_by_name": True}
    usage_unit: str = Field(..., alias="usageUnit")
    display_quantity: float = Field(..., alias="displayQuantity")
    tiered_rates: List[TieredRate] = Field(..., alias="tieredRates")
    base_unit: Optional[str] = Field(None, alias="baseUnit")
    base_unit_conversion_factor: Optional[float] = Field(None, alias="baseUnitConversionFactor")

class PricingInfo(BaseModel):
    model_config = {"populate_by_name": True}
    effective_time: str = Field(..., alias="effectiveTime")
    summary: Optional[str] = None
    pricing_expression: PricingExpression = Field(..., alias="pricingExpression")
    aggregation_info: Optional[AggregationInfo] = Field(None, alias="aggregationInfo")
    currency_conversion_rate: Optional[float] = Field(None, alias="currencyConversionRate")

class Category(BaseModel):
    model_config = {"populate_by_name": True}
    service_display_name: str = Field(..., alias="serviceDisplayName")
    resource_family: str = Field(..., alias="resourceFamily")
    resource_group: str = Field(..., alias="resourceGroup")
    usage_type: str = Field(..., alias="usageType")

class SKU(BaseModel):
    model_config = {"populate_by_name": True}
    name: str
    sku_id: str = Field(..., alias="skuId")
    display_name: str = Field(..., alias="displayName")
    category: Category
    service_regions: List[str] = Field(..., alias="serviceRegions")
    pricing_info: List[PricingInfo] = Field(..., alias="pricingInfo")
    service_provider_name: str = Field(..., alias="serviceProviderName")

class ListSKUsResponse(BaseModel):
    model_config = {"populate_by_name": True}
    skus: List[SKU]
    next_page_token: Optional[str] = Field(None, alias="nextPageToken")

class Service(BaseModel):
    model_config = {"populate_by_name": True}
    name: str
    service_id: str = Field(..., alias="serviceId")
    display_name: str = Field(..., alias="displayName")

class ListServicesResponse(BaseModel):
    model_config = {"populate_by_name": True}
    services: List[Service]
    next_page_token: Optional[str] = Field(None, alias="nextPageToken")

# Tool Input/Output Models

class EstimateCostInput(BaseModel):
    sku_id: str = Field(..., description="The SKU ID to calculate cost for (e.g., '0008-F633-76AA').")
    usage_amount: float = Field(..., description="The amount of usage to calculate cost for.")
    currency_code: Optional[str] = Field("USD", description="ISO-4217 currency code.")
    service_name: Optional[str] = None
    region: Optional[str] = None
    description: Optional[str] = None

class CostBreakdown(BaseModel):
    sku_id: str
    usage_amount: float
    unit: str
    estimated_cost: float
    currency_code: str
    price_per_unit: float
    tiered_pricing: bool
    number_of_tiers: int
    cost_breakdown: Optional[str] = None
    service_name: Optional[str] = None
    region: Optional[str] = None
    description: Optional[str] = None
    # Free tier fields
    total_usage: float
    free_tier_applied: float
    billable_usage: float
    free_tier_note: Optional[str] = None
    free_tier_source_url: Optional[str] = None

class EstimateCostOutput(BaseModel):
    estimate: CostBreakdown
