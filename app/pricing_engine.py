"""
pricing_engine.py — Core calculation and market price recommendation engine.

Defines the mathematical floor pricing rules and competitive pricing strategy
for Dorman/Help NOS automotive parts on eBay.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Default constants according to WNC Part Slingers business rules
DEFAULT_SHIPPING_COST = 4.25
DEFAULT_EBAY_FEE_PCT = 0.1325
DEFAULT_EBAY_FIXED_FEE = 0.30
DEFAULT_MIN_NET_PROFIT = 3.50
DEFAULT_TARGET_MARGIN_PCT = 0.30

# Tiered COGS lookup table based on expected selling price ranges
_COGS_TIERS = [
    (10.00, 3.50),   # <= $10.00 -> $3.50 COGS
    (15.00, 6.50),   # $10.01 - $15.00 -> $6.50 COGS
    (25.00, 9.50),   # $15.01 - $25.00 -> $9.50 COGS
    (35.00, 12.50),  # $25.01 - $35.00 -> $12.50 COGS
    (50.00, 15.50),  # $35.01 - $50.00 -> $15.50 COGS
]
_CAP_COGS = 15.50     # > $50.00 -> $15.50 COGS


def get_default_cogs(projected_price: float) -> float:
    """Return default COGS according to the WNC NOS part price brackets."""
    for upper_limit, cogs_val in _COGS_TIERS:
        if projected_price <= upper_limit:
            return cogs_val
    return _CAP_COGS


def calculate_target_profit(expected_price: float, min_net_profit: float = DEFAULT_MIN_NET_PROFIT, margin_pct: float = DEFAULT_TARGET_MARGIN_PCT) -> float:
    """Calculate target net profit: Max($3.50, 30% margin)."""
    return max(min_net_profit, expected_price * margin_pct)


def calculate_floor_price(
    cogs: float,
    shipping_cost: float = DEFAULT_SHIPPING_COST,
    fee_pct: float = DEFAULT_EBAY_FEE_PCT,
    fixed_fee: float = DEFAULT_EBAY_FIXED_FEE,
    min_net_profit: float = DEFAULT_MIN_NET_PROFIT,
    margin_pct: float = DEFAULT_TARGET_MARGIN_PCT,
) -> float:
    """
    Calculate absolute minimum floor selling price:
    Floor = (COGS + Shipping + FixedFee + TargetProfit) / (1 - FeePct)
    """
    # Estimate target profit based on approximate price range
    approx_price = (cogs + shipping_cost + fixed_fee + min_net_profit) / (1 - fee_pct)
    target_profit = calculate_target_profit(approx_price, min_net_profit, margin_pct)
    
    numerator = cogs + shipping_cost + fixed_fee + target_profit
    denominator = 1.0 - fee_pct
    if denominator <= 0:
        return 999.99
    return round(numerator / denominator, 2)


@dataclass
class PricingRecommendation:
    mpn: str
    brand: str
    title: str
    cogs: float
    shipping_cost: float
    floor_price: float
    lowest_competitor_price: float | None
    suggested_price: float
    margin_dollars: float
    margin_pct: float
    status_code: str    # 'COMPETITIVE', 'FLOOR_LOCKED', 'RARITY_BOOST'
    status_label: str
    color_hex: str


def evaluate_part_pricing(
    mpn: str,
    brand: str = "Dorman",
    title: str = "",
    lowest_competitor_price: float | None = None,
    custom_cogs: float | None = None,
    shipping_cost: float = DEFAULT_SHIPPING_COST,
    undercut_amount: float = 0.05,
) -> PricingRecommendation:
    """
    Evaluates market conditions and calculates the optimal competitive selling price.
    """
    # 1. Determine COGS
    if custom_cogs is not None and custom_cogs > 0:
        cogs = custom_cogs
    else:
        reference_price = lowest_competitor_price if lowest_competitor_price else 12.00
        cogs = get_default_cogs(reference_price)

    # 2. Calculate absolute Floor Price
    floor_price = calculate_floor_price(cogs=cogs, shipping_cost=shipping_cost)

    # 3. Apply Pricing Strategy Logic
    if lowest_competitor_price is None or lowest_competitor_price <= 0:
        # Case A: No competitors -> Rarity Boost
        suggested_price = round(floor_price * 1.15, 2)
        status_code = "RARITY_BOOST"
        status_label = "🟣 Rarity Boost"
        color_hex = "#BB86FC"
    else:
        target_undercut = round(lowest_competitor_price - undercut_amount, 2)
        if target_undercut >= floor_price:
            # Case B: Competitive Undercut
            suggested_price = target_undercut
            status_code = "COMPETITIVE"
            status_label = "🟢 Competitive"
            color_hex = "#03DAC6"
        else:
            # Case C: Competitor is below floor -> Lock at Floor
            suggested_price = floor_price
            status_code = "FLOOR_LOCKED"
            status_label = "🟡 Floor Locked"
            color_hex = "#CF6679"

    # 4. Calculate final net profit margin metrics
    ebay_fee = (suggested_price * DEFAULT_EBAY_FEE_PCT) + DEFAULT_EBAY_FIXED_FEE
    net_profit = suggested_price - (cogs + shipping_cost + ebay_fee)
    margin_pct = (net_profit / suggested_price * 100) if suggested_price > 0 else 0.0

    return PricingRecommendation(
        mpn=mpn,
        brand=brand,
        title=title,
        cogs=cogs,
        shipping_cost=shipping_cost,
        floor_price=floor_price,
        lowest_competitor_price=lowest_competitor_price,
        suggested_price=suggested_price,
        margin_dollars=round(net_profit, 2),
        margin_pct=round(margin_pct, 1),
        status_code=status_code,
        status_label=status_label,
        color_hex=color_hex,
    )
