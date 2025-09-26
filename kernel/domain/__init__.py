"""Domain adaptation utilities for the kernel."""
from .adapters import (
    DomainAdapter,
    RetailDomainAdapter,
    ManufacturingDomainAdapter,
    HealthcareDomainAdapter,
    LogisticsDomainAdapter,
    HospitalityDomainAdapter,
    get_adapter,
)

__all__ = [
    "DomainAdapter",
    "RetailDomainAdapter",
    "ManufacturingDomainAdapter",
    "HealthcareDomainAdapter",
    "LogisticsDomainAdapter",
    "HospitalityDomainAdapter",
    "get_adapter",
]
