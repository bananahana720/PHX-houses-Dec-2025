"""Centralized Configuration Constants for PHX Home Analysis.

All magic numbers, thresholds, and configuration values should be defined here
with clear documentation of their sources, rationale, and usage.

This module is the single source of truth for:
- Scoring thresholds and tier boundaries
- Kill-switch severity weights
- Confidence/quality thresholds
- Cost estimation rates and minimums
- Arizona-specific constants
"""

from typing import Final

# =============================================================================
# SCORING THRESHOLDS
# =============================================================================
# Source: Business requirements - derived from 600-point max scoring system
# Tier boundaries are based on percentage of maximum score

# Maximum possible score in the 600-point system
MAX_POSSIBLE_SCORE: Final[int] = 600

# Unicorn tier: > 80% of max score (480+ points)
# Represents exceptional properties worthy of immediate action
TIER_UNICORN_MIN: Final[int] = 480

# Contender tier: 60-80% of max score (360-479 points)
# Represents strong properties worthy of serious consideration
TIER_CONTENDER_MIN: Final[int] = 360

# Pass tier: < 60% of max score (<360 points)
# Meets minimum kill-switch criteria but lacks standout features
TIER_PASS_MAX: Final[int] = 359


# =============================================================================
# KILL-SWITCH SEVERITY THRESHOLDS
# =============================================================================
# Source: Buyer profile risk assessment
# Used for weighted severity scoring of SOFT criteria

# Severity fail threshold: Any severity >= 3.0 causes property FAIL
# This prevents accumulation of too many minor issues
SEVERITY_FAIL_THRESHOLD: Final[float] = 3.0

# Severity warning threshold: 1.5-3.0 severity causes property WARNING
# Indicates approaching fail threshold, needs closer inspection
SEVERITY_WARNING_THRESHOLD: Final[float] = 1.5


# =============================================================================
# KILL-SWITCH SEVERITY WEIGHTS (SOFT CRITERIA)
# =============================================================================
# Source: Business rules based on buyer profile priorities
# Applied to properties that DON'T fail hard criteria but have minor issues

# City sewer required: Septic is infrastructure concern, adds 2.5 severity
# Septic systems are less desirable in Phoenix metro and add maintenance burden
SEVERITY_WEIGHT_SEWER: Final[float] = 2.5

# New build avoidance (year_built < 2024): Newer homes more likely to have issues
# Excludes current-year builds but allows prior years; adds 2.0 severity
SEVERITY_WEIGHT_YEAR_BUILT: Final[float] = 2.0

# 2-car garage minimum: Convenience factor in Phoenix metro living
# Adds 1.5 severity if less than 2 spaces
SEVERITY_WEIGHT_GARAGE: Final[float] = 1.5

# Lot size (7k-15k sqft range): Preference factor, wide acceptable range
# Adds 1.0 severity if outside target range
SEVERITY_WEIGHT_LOT_SIZE: Final[float] = 1.0


# =============================================================================
# CONFIDENCE THRESHOLDS (AI Enrichment & Quality Metrics)
# =============================================================================
# Source: AI/ML confidence scoring standards and quality gates

# High confidence threshold: >= 0.8
# Indicates inference/data is very reliable and can be used without verification
CONFIDENCE_HIGH_THRESHOLD: Final[float] = 0.80

# Quality gate threshold: >= 0.95
# Minimum overall data quality score to pass CI/CD quality gates
# Ensures 95%+ of fields are high-confidence
QUALITY_GATE_THRESHOLD: Final[float] = 0.95


# =============================================================================
# CONFIDENCE WEIGHTS BY DATA SOURCE
# =============================================================================
# Source: Data provenance analysis - how reliable is each source?
# Used by ConfidenceScorer to assign confidence scores to enriched fields

# Official county assessor API records
# Most authoritative source for property facts
DATA_CONFIDENCE_ASSESSOR_API: Final[float] = 0.95

# Web-scraped listing data (Zillow, Redfin, MLS)
# Generally reliable but subject to data entry errors
DATA_CONFIDENCE_WEB_SCRAPE: Final[float] = 0.85

# Manual human inspection/assessment
# Subject to observer bias, but direct evidence
DATA_CONFIDENCE_MANUAL: Final[float] = 0.85

# Field-level confidence weights (assessor API vs. listing vs. manual)
# Individual field reliability varies by source completeness
FIELD_CONFIDENCE_LOT_SQFT: Final[float] = 0.95      # Very accurate from assessor
FIELD_CONFIDENCE_YEAR_BUILT: Final[float] = 0.95    # Very accurate from assessor
FIELD_CONFIDENCE_SQFT: Final[float] = 0.85          # Sometimes varies between sources
FIELD_CONFIDENCE_HAS_POOL: Final[float] = 0.80      # Usually visible in photos/listings
FIELD_CONFIDENCE_ORIENTATION: Final[float] = 0.85   # Satellite imagery + manual


# =============================================================================
# COST ESTIMATION - ARIZONA SPECIFIC
# =============================================================================
# Source: 2024-2025 Arizona market data and industry standards
# Used for monthly cost estimation (mortgage, taxes, insurance, utilities, etc.)

# ---- MORTGAGE & FINANCING ----

# 30-year fixed mortgage rate (Dec 2024 market rate)
MORTGAGE_RATE_30YR: Final[float] = 0.0699

# 30-year mortgage term in months
MORTGAGE_TERM_MONTHS: Final[int] = 360

# Loan-to-value (LTV) threshold for PMI requirement
PMI_THRESHOLD_LTV: Final[float] = 0.80

# Annual PMI rate (percentage of loan amount)
PMI_ANNUAL_RATE: Final[float] = 0.005  # 0.5% of loan

# Default down payment assumption for first-time buyer
DOWN_PAYMENT_DEFAULT: Final[float] = 50_000.0

# ---- INSURANCE ----

# Annual homeowner's insurance per $1,000 of home value
# Arizona average: ~$6.50/year per $1k (varies by coverage/location)
INSURANCE_RATE_PER_1K: Final[float] = 6.50

# Minimum annual insurance base (small homes)
INSURANCE_MINIMUM_ANNUAL: Final[float] = 800.0

# ---- PROPERTY TAX ----

# Effective property tax rate in Maricopa County
# Based on Limited Property Value (LPV), not Full Cash Value (FCV)
# Actual rate varies by municipality and special districts
PROPERTY_TAX_RATE: Final[float] = 0.0066  # ~0.66% effective rate

# ---- UTILITIES (Arizona-specific) ----

# Monthly utility cost per square foot
# Electric and gas only (AZ has higher electric due to A/C usage June-Sept)
UTILITY_RATE_PER_SQFT: Final[float] = 0.08

# Minimum monthly utilities (baseline for small homes)
UTILITY_MINIMUM_MONTHLY: Final[float] = 120.0

# Maximum monthly utilities cap (very large homes)
UTILITY_MAXIMUM_MONTHLY: Final[float] = 500.0

# ---- WATER COSTS ----

# City water base service charge (Maricopa County average)
WATER_MONTHLY_BASE: Final[float] = 30.0

# City water rate per 1,000 gallons
WATER_RATE_PER_KGAL: Final[float] = 5.0

# Average AZ household water usage per month (gallons)
WATER_AVG_USAGE_KGAL: Final[float] = 12.0

# Calculated monthly water estimate (~$90)
WATER_MONTHLY_ESTIMATE: Final[float] = (
    WATER_MONTHLY_BASE + (WATER_RATE_PER_KGAL * WATER_AVG_USAGE_KGAL)
)

# ---- TRASH/RECYCLING ----

# City trash and recycling pickup (Maricopa County average)
TRASH_MONTHLY: Final[float] = 40.0

# ---- POOL COSTS (Arizona-specific) ----

# Monthly pool service cost (cleaning, chemical balance, maintenance)
# Standard pool service in Phoenix metro area
POOL_SERVICE_MONTHLY: Final[float] = 125.0

# Monthly pool energy cost (pump, heater, cleaning system)
# Higher during summer months (June-September)
POOL_ENERGY_MONTHLY: Final[float] = 75.0

# Combined monthly pool cost (service + energy)
POOL_TOTAL_MONTHLY: Final[float] = POOL_SERVICE_MONTHLY + POOL_ENERGY_MONTHLY

# Note: Seasonal variation - Summer pool costs can be 20-30% higher

# ---- MAINTENANCE RESERVES ----

# Annual maintenance reserve as percentage of home value
# Rule of thumb: 1% annually for maintenance/repairs
MAINTENANCE_RESERVE_ANNUAL_RATE: Final[float] = 0.01

# Monthly maintenance reserve rate (derived from annual)
MAINTENANCE_RESERVE_MONTHLY_RATE: Final[float] = MAINTENANCE_RESERVE_ANNUAL_RATE / 12

# Minimum monthly maintenance reserve
MAINTENANCE_MINIMUM_MONTHLY: Final[float] = 200.0

# ---- SOLAR LEASES (Arizona-specific) ----

# Typical solar lease monthly payment minimum (Phoenix area)
SOLAR_LEASE_TYPICAL_MIN: Final[float] = 100.0

# Typical solar lease monthly payment maximum (Phoenix area)
SOLAR_LEASE_TYPICAL_MAX: Final[float] = 200.0

# Default solar lease payment when actual lease not specified
SOLAR_LEASE_DEFAULT: Final[float] = 150.0


# =============================================================================
# ARIZONA-SPECIFIC CONSTANTS
# =============================================================================
# Source: Arizona climate and real estate market research

# ---- HVAC LIFESPAN ----

# Expected HVAC lifespan in Arizona (years)
# Arizona heat reduces lifespan vs. national average (10-15 years vs. 15-20 years)
HVAC_LIFESPAN_YEARS: Final[int] = 12

# Typical HVAC replacement cost (Phoenix metro)
HVAC_REPLACEMENT_COST: Final[float] = 8_000.0

# ---- ROOF LIFESPAN ----

# Expected roof lifespan in Arizona (years)
# Arizona heat and intense sun reduce lifespan vs. national average
ROOF_LIFESPAN_YEARS_NEW: Final[int] = 5
ROOF_LIFESPAN_YEARS_GOOD: Final[int] = 10
ROOF_LIFESPAN_YEARS_FAIR: Final[int] = 15
ROOF_LIFESPAN_YEARS_AGING: Final[int] = 20

# ---- POOL EQUIPMENT ----

# Average pool equipment lifespan in Arizona (years)
# Arizona heat/sun reduces equipment lifespan
POOL_EQUIPMENT_LIFESPAN_YEARS: Final[int] = 8

# Average pool equipment replacement cost
POOL_EQUIPMENT_REPLACEMENT_COST: Final[float] = 5_500.0

# ---- SUN ORIENTATION IMPACT ----

# Cooling cost impact multiplier for west-facing homes (higher AC usage)
ORIENTATION_WEST_PENALTY: Final[float] = -15  # Point deduction for heat penalty

# Cooling cost advantage for north-facing homes (minimal sun exposure)
ORIENTATION_NORTH_BONUS: Final[float] = 15  # Point bonus for efficiency


# =============================================================================
# IMAGE PROCESSING & EXTRACTION
# =============================================================================

# Maximum width/height for processed property images (pixels)
IMAGE_MAX_DIMENSION: Final[int] = 1024

# Hamming distance threshold for perceptual hash deduplication
# Images within this distance are considered duplicates
IMAGE_HASH_SIMILARITY_THRESHOLD: Final[int] = 8

# ---- RATE LIMITING & CONCURRENCY ----

# Milliseconds delay between image downloads (anti-detection)
IMAGE_DOWNLOAD_DELAY_MS: Final[int] = 500

# Maximum parallel image downloads
IMAGE_MAX_CONCURRENT_DOWNLOADS: Final[int] = 5

# Maximum properties processed simultaneously
IMAGE_MAX_CONCURRENT_PROPERTIES: Final[int] = 3

# ---- RETRY & TIMEOUT ----

# Maximum retry attempts for failed downloads
IMAGE_MAX_RETRIES: Final[int] = 3

# Base delay in seconds for exponential backoff
IMAGE_RETRY_BASE_DELAY: Final[float] = 1.0

# Timeout for individual image downloads (seconds)
IMAGE_DOWNLOAD_TIMEOUT: Final[int] = 30

# Timeout for browser-based extraction (seconds)
IMAGE_BROWSER_TIMEOUT: Final[int] = 30


# =============================================================================
# STEALTH EXTRACTION (Browser Automation)
# =============================================================================
# Source: Anti-detection requirements for bypassing PerimeterX

# Browser viewport width (pixels) - typical desktop
BROWSER_VIEWPORT_WIDTH: Final[int] = 1280

# Browser viewport height (pixels) - typical desktop
BROWSER_VIEWPORT_HEIGHT: Final[int] = 720

# Minimum delay between actions (seconds) - human behavior simulation
HUMAN_DELAY_MIN: Final[float] = 1.0

# Maximum delay between actions (seconds) - human behavior simulation
HUMAN_DELAY_MAX: Final[float] = 3.0

# Minimum hold duration for Press & Hold CAPTCHA (seconds)
CAPTCHA_HOLD_MIN: Final[float] = 4.0

# Maximum hold duration for Press & Hold CAPTCHA (seconds)
CAPTCHA_HOLD_MAX: Final[float] = 7.0

# HTTP request timeout (seconds)
REQUEST_TIMEOUT: Final[float] = 30.0


# =============================================================================
# SCORING SYSTEM CONSTANTS
# =============================================================================
# Source: Business requirements - 600-point weighted scoring system

# ---- SECTION A: LOCATION & ENVIRONMENT (230 pts max) ----

# School district score (out of 50 max)
# Based on GreatSchools rating (1-10 scale) × 5
SCORE_SECTION_A_SCHOOL_DISTRICT: Final[int] = 50

# Quietness score (out of 40 max)
# Based on distance to nearest highway/freeway
SCORE_SECTION_A_QUIETNESS: Final[int] = 40

# Safety score (out of 50 max)
# Manual neighborhood assessment (crime, lighting, upkeep)
SCORE_SECTION_A_SAFETY: Final[int] = 50

# Supermarket proximity score (out of 30 max)
# Distance to nearest preferred grocery store
SCORE_SECTION_A_SUPERMARKET_PROXIMITY: Final[int] = 30

# Parks & walkability score (out of 30 max)
# Manual assessment of parks, sidewalks, trails
SCORE_SECTION_A_PARKS_WALKABILITY: Final[int] = 30

# Sun orientation score (out of 30 max)
# Impact on cooling costs (north=best, west=worst)
SCORE_SECTION_A_SUN_ORIENTATION: Final[int] = 30

# Total Section A maximum score
SCORE_SECTION_A_TOTAL: Final[int] = (
    SCORE_SECTION_A_SCHOOL_DISTRICT
    + SCORE_SECTION_A_QUIETNESS
    + SCORE_SECTION_A_SAFETY
    + SCORE_SECTION_A_SUPERMARKET_PROXIMITY
    + SCORE_SECTION_A_PARKS_WALKABILITY
    + SCORE_SECTION_A_SUN_ORIENTATION
)

# ---- SECTION B: LOT & SYSTEMS (180 pts max) ----

# Roof condition score (out of 50 max)
# Age and condition (new=50, aging=10, replacement needed=0)
SCORE_SECTION_B_ROOF_CONDITION: Final[int] = 50

# Backyard utility score (out of 40 max)
# Estimated usable backyard space
SCORE_SECTION_B_BACKYARD_UTILITY: Final[int] = 40

# Plumbing & electrical score (out of 40 max)
# Based on year built and upgrade evidence
SCORE_SECTION_B_PLUMBING_ELECTRICAL: Final[int] = 40

# Pool condition score (out of 20 max)
# Equipment age/condition (no pool=10 neutral, new=20)
SCORE_SECTION_B_POOL_CONDITION: Final[int] = 20

# Cost efficiency score (out of 30 max)
# Monthly cost estimate efficiency
SCORE_SECTION_B_COST_EFFICIENCY: Final[int] = 30

# Total Section B maximum score
SCORE_SECTION_B_TOTAL: Final[int] = (
    SCORE_SECTION_B_ROOF_CONDITION
    + SCORE_SECTION_B_BACKYARD_UTILITY
    + SCORE_SECTION_B_PLUMBING_ELECTRICAL
    + SCORE_SECTION_B_POOL_CONDITION
    + SCORE_SECTION_B_COST_EFFICIENCY
)

# ---- SECTION C: INTERIOR & FEATURES (190 pts max) ----

# Kitchen layout score (out of 40 max)
# Open concept, island/counter space, appliances, pantry
SCORE_SECTION_C_KITCHEN_LAYOUT: Final[int] = 40

# Master suite score (out of 40 max)
# Bedroom size, closet space, bathroom quality, privacy
SCORE_SECTION_C_MASTER_SUITE: Final[int] = 40

# Natural light score (out of 30 max)
# Windows, skylights, room brightness, open floor plan
SCORE_SECTION_C_NATURAL_LIGHT: Final[int] = 30

# High ceilings score (out of 30 max)
# Ceiling height (vaulted/cathedral=30, 10+ ft=25, standard=10)
SCORE_SECTION_C_HIGH_CEILINGS: Final[int] = 30

# Fireplace score (out of 20 max)
# Presence and quality (gas=20, wood=15, decorative=5, none=0)
SCORE_SECTION_C_FIREPLACE: Final[int] = 20

# Laundry area score (out of 20 max)
# Location and quality (dedicated room=20, closet=10, garage=5)
SCORE_SECTION_C_LAUNDRY_AREA: Final[int] = 20

# Aesthetics score (out of 10 max)
# Overall subjective appeal (curb appeal, finishes, modern vs. dated)
SCORE_SECTION_C_AESTHETICS: Final[int] = 10

# Total Section C maximum score
SCORE_SECTION_C_TOTAL: Final[int] = (
    SCORE_SECTION_C_KITCHEN_LAYOUT
    + SCORE_SECTION_C_MASTER_SUITE
    + SCORE_SECTION_C_NATURAL_LIGHT
    + SCORE_SECTION_C_HIGH_CEILINGS
    + SCORE_SECTION_C_FIREPLACE
    + SCORE_SECTION_C_LAUNDRY_AREA
    + SCORE_SECTION_C_AESTHETICS
)

# Verify total equals 600
assert SCORE_SECTION_A_TOTAL + SCORE_SECTION_B_TOTAL + SCORE_SECTION_C_TOTAL == MAX_POSSIBLE_SCORE, (
    f"Scoring sections don't sum to {MAX_POSSIBLE_SCORE}: "
    f"A={SCORE_SECTION_A_TOTAL}, B={SCORE_SECTION_B_TOTAL}, C={SCORE_SECTION_C_TOTAL}"
)
