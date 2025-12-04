# Development Workflow

### Adding a New Property

1. **Add to CSV**
   ```bash
   # Edit data/phx_homes.csv
   # Add row: address,price,beds,baths,sqft,price_per_sqft
   ```

2. **Extract County Data**
   ```bash
   python scripts/extract_county_data.py --address "123 Main St, City, AZ 85000"
   ```

3. **Extract Images**
   ```bash
   python scripts/extract_images.py --address "123 Main St, City, AZ 85000"
   ```

4. **Run Multi-Agent Analysis**
   ```bash
   /analyze-property "123 Main St, City, AZ 85000"
   ```

### Adding a New Scoring Criterion

**Example: Add "Noise Level" scorer (25 pts)**

1. **Update Constants**
   ```python
   # src/phx_home_analysis/config/constants.py
   SCORE_SECTION_A_NOISE_LEVEL: Final[int] = 25
   ```

2. **Update Scoring Weights**
   ```python
   # src/phx_home_analysis/config/scoring_weights.py
   @dataclass(frozen=True)
   class ScoringWeights:
       # Section A
       noise_level: int = 25  # NEW
   ```

3. **Create Scorer Strategy**
   ```python
   # src/phx_home_analysis/services/scoring/strategies/location.py
   class NoiseLevelScorer(ScoringStrategy):
       """Score based on noise pollution (airports, highways, railroads)."""

       def score(self, property: Property) -> float:
           """Return score 0-10 based on noise level."""
           if property.noise_level_db is None:
               return 5.0  # Neutral default

           # Scoring logic: < 50dB = 10pts, > 70dB = 0pts
           if property.noise_level_db < 50:
               return 10.0
           elif property.noise_level_db > 70:
               return 0.0
           else:
               # Linear interpolation
               return 10.0 - ((property.noise_level_db - 50) / 2.0)
   ```

4. **Register Strategy**
   ```python
   # src/phx_home_analysis/services/scoring/__init__.py
   LOCATION_STRATEGIES: list[tuple[ScoringStrategy, int]] = [
       (SchoolDistrictScorer(), 42),
       (NoiseLevel Scorer(), 25),  # NEW
       # ... other strategies
   ]
   ```

5. **Update Domain Model**
   ```python
   # src/phx_home_analysis/domain/entities.py
   @dataclass
   class Property:
       noise_level_db: float | None = None  # NEW
   ```

6. **Write Tests**
   ```python
   # tests/unit/test_noise_level_scorer.py
   def test_noise_level_scorer_quiet():
       prop = Property(noise_level_db=45.0, ...)
       scorer = NoiseLevelScorer()
       assert scorer.score(prop) == 10.0

   def test_noise_level_scorer_loud():
       prop = Property(noise_level_db=75.0, ...)
       scorer = NoiseLevelScorer()
       assert scorer.score(prop) == 0.0
   ```

7. **Update Documentation**
   ```markdown
   # docs/scoring-system.md
   ## Section A: Location (255 pts) <- Update total

   ### Noise Level (25 pts)
   - < 50dB: 10 pts (very quiet)
   - 60dB: 5 pts (moderate)
   - > 70dB: 0 pts (very loud)
   ```

---
