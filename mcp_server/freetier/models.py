import re
from pydantic import BaseModel
from typing import List, Optional

class FreeTierItem(BaseModel):
    resource: str
    amount: float
    unit: str

class FreeTierInfo(BaseModel):
    service_name: str
    items: List[FreeTierItem]
    scope: str  # "account" or "project"
    period: str # "month", "day", or "always"
    conditions: List[str] = []
    source_url: str

# Regex patterns for extracting free tier info from GCP docs
# Ported and expanded from Go implementation
FREE_TIER_PATTERNS = [
    # vCPU and memory time patterns (Cloud Run, Cloud Functions)
    {
        "pattern": r'(?i)([0-9,]+)\s*vCPU[- ]?seconds?\s*(?:per\s*month|/month|monthly)?\s*(?:free|at no charge)',
        "resource": "vCPU-seconds",
        "unit": "seconds"
    },
    {
        "pattern": r'(?i)([0-9,]+)\s*GiB[- ]?seconds?\s*(?:per\s*month|/month|monthly)?\s*(?:free|at no charge)',
        "resource": "GiB-seconds",
        "unit": "seconds"
    },
    # Storage patterns
    {
        "pattern": r'(?i)first\s*([0-9.]+)\s*(?:GB|GiB)\s*(?:of\s*storage\s*)?(?:per\s*month|/month|monthly)?\s*(?:is\s*)?free',
        "resource": "storage",
        "unit": "GiB"
    },
    # Request patterns
    {
        "pattern": r'(?i)first\s*([0-9.]+)\s*million\s*(?:invocations?|requests?)\s*(?:per\s*month|/month|monthly)?\s*(?:are\s*|is\s*)?free',
        "resource": "requests",
        "unit": "million"
    },
    # Add more as needed based on Go's patterns.go
]
