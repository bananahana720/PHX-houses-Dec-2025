# Common Tasks

### Adding a New Data Source

1. **Create client**
   ```python
   # src/phx_home_analysis/services/my_source/client.py
   class MySourceClient:
       def fetch_data(self, address: str) -> dict:
           # API call or web scraping
           pass
   ```

2. **Create models**
   ```python
   # src/phx_home_analysis/services/my_source/models.py
   from pydantic import BaseModel

   class MySourceData(BaseModel):
       field1: str
       field2: int
   ```

3. **Add to extraction script**
   ```python
   # scripts/extract_my_source_data.py
   from src.phx_home_analysis.services.my_source.client import MySourceClient

   client = MySourceClient()
   data = client.fetch_data(address)
   # Update enrichment_data.json
   ```

### Updating Scoring Weights

1. **Edit constants**
   ```python
   # src/phx_home_analysis/config/constants.py
   SCORE_SECTION_A_SCHOOL_DISTRICT: Final[int] = 50  # Was 42
   ```

2. **Update scoring_weights.py**
   ```python
   # src/phx_home_analysis/config/scoring_weights.py
   @dataclass(frozen=True)
   class ScoringWeights:
       school_district: int = 50  # Was 42
   ```

3. **Verify total**
   ```python
   # Ensure total still equals 600
   weights = ScoringWeights()
   assert weights.total_possible_score == 600
   ```

4. **Update docs**
   ```markdown
   # docs/scoring-system.md
   ## Section A: Location (258 pts) <- Update total

   ### School District (50 pts) <- Update weight
   ```

### Debugging Data Issues

**Problem: enrichment_data.json missing fields**

```bash
# Check structure
cat data/enrichment_data.json | jq '.[] | select(.full_address | contains("123")) | keys'

# Check specific field
cat data/enrichment_data.json | jq '.[] | select(.full_address | contains("123")) | .location.school_rating'

# If missing, re-run extraction
python scripts/extract_county_data.py --address "123 Main St"
```

**Problem: Images not found for Phase 2**

```bash
# Check image manifest
cat data/property_images/metadata/image_manifest.json | jq 'keys'

# Check address lookup
cat data/property_images/metadata/address_folder_lookup.json | jq '.mappings["123 Main St, City, AZ 85000"]'

# Re-run image extraction
python scripts/extract_images.py --address "123 Main St, City, AZ 85000" --sources zillow,redfin
```

---
