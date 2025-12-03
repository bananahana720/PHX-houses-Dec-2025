"""Building permit history service using Maricopa County GIS.

Provides permit history for estimating system ages (roof, HVAC)
and identifying major renovations.
"""

from .client import MaricopaPermitClient
from .models import Permit, PermitHistory, PermitType

__all__ = ["MaricopaPermitClient", "Permit", "PermitHistory", "PermitType"]
