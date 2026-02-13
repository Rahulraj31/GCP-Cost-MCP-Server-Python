from mcp_server.pricing.client import PricingClient
from mcp_server.models.billing import PricingExpression, TieredRate, Money

def test_calculate_cost_flat_rate():
    # Mock pricing expression with single tier
    expr = PricingExpression(
        usage_unit="count",
        display_quantity=1.0,
        tiered_rates=[
            TieredRate(
                start_usage_amount=0.0,
                unit_price=Money(currency_code="USD", units="1", nanos=0) # $1.00 per unit
            )
        ]
    )
    
    client = PricingClient(None) 
    cost = client.calculate_cost(expr, 10.0)
    assert cost == 10.0

def test_calculate_cost_tiered():
    # Mock expression with two tiers: 
    # 0-5: $2.00
    # 5+: $1.00
    expr = PricingExpression(
        usage_unit="count",
        display_quantity=1.0,
        tiered_rates=[
            TieredRate(
                start_usage_amount=0.0,
                unit_price=Money(currency_code="USD", units="2", nanos=0)
            ),
            TieredRate(
                start_usage_amount=5.0,
                unit_price=Money(currency_code="USD", units="1", nanos=0)
            )
        ]
    )
    
    client = PricingClient(None)
    
    # Test within first tier
    assert client.calculate_cost(expr, 3.0) == 6.0
    
    # Test across tiers
    # 5 units @ $2.00 = $10.00
    # 2 units @ $1.00 = $2.00
    # Total = $12.00
    assert client.calculate_cost(expr, 7.0) == 12.0
