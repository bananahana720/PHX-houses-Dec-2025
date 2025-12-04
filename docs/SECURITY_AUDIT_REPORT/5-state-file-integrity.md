# 5. State File Integrity

**Files:**
- `src/phx_home_analysis/services/image_extraction/state_manager.py`
- `src/phx_home_analysis/services/image_extraction/orchestrator.py`

### Findings

#### ✅ STRENGTHS

1. **Atomic State Writes** (state_manager.py:159-195)
   ```python
   fd, temp_path = tempfile.mkstemp(dir=self.state_path.parent, suffix=".tmp")
   try:
       with os.fdopen(fd, "w", encoding="utf-8") as f:
           json.dump(self._state.to_dict(), f, indent=2)
       os.replace(temp_path, self.state_path)  # Atomic
   ```
   - Prevents corruption from crashes
   - Atomic replace on both Unix and Windows
   - Cleanup on exception

2. **State Validation** (state_manager.py:52-66)
   ```python
   return cls(
       completed_properties=set(data.get("completed_properties", [])),
       failed_properties=set(data.get("failed_properties", [])),
       ...
   )
   ```
   - Type conversion (list → set)
   - Default values for missing fields
   - Graceful handling of malformed data

3. **Concurrency Control** (orchestrator.py:130-131, 365-416)
   ```python
   self._state_lock = asyncio.Lock()

   async with self._state_lock:
       # State mutations...
   ```
   - asyncio.Lock prevents race conditions
   - All state writes are protected
   - Manifest updates also locked

4. **Timestamping** (state_manager.py:68-76)
   ```python
   self.property_last_checked[address] = datetime.now().astimezone().isoformat()
   ```
   - ISO 8601 timestamps with timezone
   - Audit trail for all checks

5. **Error Recovery** (state_manager.py:143-157)
   ```python
   try:
       with open(self.state_path, encoding="utf-8") as f:
           data = json.load(f)
           self._state = ExtractionState.from_dict(data)
   except (OSError, json.JSONDecodeError) as e:
       logger.warning(f"Failed to load state: {e}")
   self._state = ExtractionState()  # Default to empty
   ```
   - Handles corrupted state files
   - Starts fresh if unreadable

#### ⚠️ MEDIUM PRIORITY (P2)

**M-8: No State File Integrity Verification**

**Location:** `state_manager.py:145-147`

**Issue:** State files are loaded without integrity verification. An attacker with file system access could tamper with state to skip properties or mark malicious properties as completed.

**Exploitation Scenario:**
```json
// Attacker modifies extraction_state.json
{
  "completed_properties": [
    "123 Main St",
    "ATTACKER_CONTROLLED_PROPERTY"  // Marks as completed to skip
  ],
  "last_updated": "2025-12-02T10:00:00-07:00"
}
```

**Impact:**
- Skip extraction of legitimate properties
- Mark malicious properties as clean
- Manipulate extraction statistics

**Remediation:**
```python
import hashlib
import hmac

class StateManager:
    def __init__(self, state_path: Path, integrity_key: str | None = None):
        self.state_path = Path(state_path)
        self.integrity_key = integrity_key or os.getenv("STATE_INTEGRITY_KEY")
        self._state: ExtractionState | None = None

    def _compute_hmac(self, data: dict) -> str:
        """Compute HMAC for state data integrity."""
        if not self.integrity_key:
            return ""

        canonical = json.dumps(data, sort_keys=True)
        return hmac.new(
            self.integrity_key.encode(),
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()

    def save(self, state: ExtractionState | None = None) -> None:
        # ... existing code ...

        state_dict = self._state.to_dict()

        # Add HMAC if key configured
        if self.integrity_key:
            state_dict['_hmac'] = self._compute_hmac(state_dict)

        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2)
        # ... rest of save logic ...

    def load(self) -> ExtractionState:
        # ... existing load logic ...

        with open(self.state_path, encoding="utf-8") as f:
            data = json.load(f)

            # Verify HMAC if present
            if '_hmac' in data and self.integrity_key:
                stored_hmac = data.pop('_hmac')
                computed_hmac = self._compute_hmac(data)

                if not hmac.compare_digest(stored_hmac, computed_hmac):
                    raise ValueError("State file integrity check failed (HMAC mismatch)")

            self._state = ExtractionState.from_dict(data)
```

**Risk Score:** MEDIUM (requires file system access, limited impact)

---

**M-9: No Schema Versioning**

**Location:** `state_manager.py:38-49`, `orchestrator.py:178-184`

**Issue:** State files don't include schema version. Future changes could break compatibility.

**Remediation:**
```python
# state_manager.py
CURRENT_STATE_VERSION = "2.0"

def to_dict(self) -> dict:
    return {
        "version": CURRENT_STATE_VERSION,
        "completed_properties": list(self.completed_properties),
        # ... rest of fields
    }

@classmethod
def from_dict(cls, data: dict) -> "ExtractionState":
    version = data.get("version", "1.0")

    if version == "1.0":
        # Migrate from v1.0 to v2.0
        data = cls._migrate_v1_to_v2(data)

    # Current version handling...
```

**Risk Score:** MEDIUM (forward compatibility issue)

---

#### ✅ LOW PRIORITY (P3)

**L-2: No State File Backup**

**Location:** `state_manager.py:159-195`

**Issue:** No automatic backup before overwriting. A backup would aid recovery from corruption.

**Recommendation:**
```python
def save(self, state: ExtractionState | None = None) -> None:
    # ... existing validation ...

    # Backup existing file before overwrite
    if self.state_path.exists():
        backup_path = self.state_path.with_suffix('.json.bak')
        shutil.copy2(self.state_path, backup_path)

    # ... rest of save logic ...
```

**Risk Score:** LOW (operational improvement, not security issue)

---
