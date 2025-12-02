"""Temporary script to add new fields to entities.py"""
import re

file_path = r"C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\src\phx_home_analysis\domain\entities.py"

with open(file_path, encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
content = content.replace(
    'from .enums import Orientation, SewerType, SolarStatus, Tier',
    'from .enums import CrimeRiskLevel, FloodZone, Orientation, SewerType, SolarStatus, Tier'
)

# 2. Add new fields before __post_init__
new_fields = '''
    # Location - Crime/Safety
    violent_crime_index: float | None = None  # 0-100, 100=safest
    property_crime_index: float | None = None  # 0-100, 100=safest
    crime_risk_level: CrimeRiskLevel = CrimeRiskLevel.UNKNOWN

    # Location - Flood Zone
    flood_zone: FloodZone = FloodZone.UNKNOWN
    flood_zone_panel: str | None = None
    flood_insurance_required: bool | None = None

    # Location - Walk/Transit/Bike Scores
    walk_score: int | None = None  # 0-100
    transit_score: int | None = None  # 0-100
    bike_score: int | None = None  # 0-100

    # Location - Noise
    noise_score: int | None = None  # 0-100, 100=quietest
    noise_sources: list[str] | None = field(default=None)

    # Location - Zoning
    zoning_code: str | None = None
    zoning_description: str | None = None
    zoning_category: str | None = None  # residential, commercial, industrial, mixed

    # Demographics
    census_tract: str | None = None
    median_household_income: int | None = None
    median_home_value: int | None = None

    # Schools - Enhanced
    elementary_rating: float | None = None  # 1-10
    middle_rating: float | None = None  # 1-10
    high_rating: float | None = None  # 1-10
    school_count_1mi: int | None = None
'''

# Find the location to insert (after parks_walkability_score, before __post_init__)
pattern = r'(    parks_walkability_score: float \| None = None  # 0-10 scale\n)\n(    def __post_init__\(self\) -> None:)'
replacement = r'\1' + new_fields + r'\n\2'

content = re.sub(pattern, replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fields added successfully!")
