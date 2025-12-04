# Known Limitations

### 1. Single-Threaded Scoring
Scoring is currently single-threaded. For large datasets (100+ properties), consider parallelizing.

### 2. No Database
All data stored in JSON/CSV files. For production scale, migrate to PostgreSQL or similar.

### 3. Manual Interior Scoring
Section C (Interior) scores require manual photo review or Sonnet vision analysis. Not fully automated.

### 4. Arizona-Specific
Scoring weights, cost estimates, and domain knowledge are tailored to Phoenix metro. Not portable to other markets without recalibration.

### 5. Image Extraction Fragility
Stealth automation is fragile - site structure changes break extractors. Requires maintenance.

### 6. No Real-Time Updates
Data is static snapshots. No real-time listing updates or price change alerts.
