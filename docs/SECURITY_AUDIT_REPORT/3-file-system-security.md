# 3. File System Security

**Files:**
- `src/phx_home_analysis/services/image_extraction/orchestrator.py`
- `src/phx_home_analysis/services/image_extraction/naming.py`
- `src/phx_home_analysis/services/image_extraction/symlink_views.py`

### Findings

#### ✅ STRENGTHS

1. **Atomic File Writes** (orchestrator.py:155-175)
   ```python
   fd, temp_path = tf.mkstemp(dir=path.parent, suffix=".tmp")
   try:
       with os.fdopen(fd, "w", encoding="utf-8") as f:
           json.dump(data, f, indent=2)
       os.replace(temp_path, path)  # Atomic on POSIX and Windows
   ```
   - Temp file + rename prevents corruption
   - Cleanup on exception
   - Works on Windows and Unix

2. **Property Hash Generation** (orchestrator.py:213-224)
   ```python
   hash_input = property.full_address.lower().strip()
   return hashlib.sha256(hash_input.encode()).hexdigest()[:8]
   ```
   - Stable, deterministic hashing
   - No user-controlled input in path
   - 8-character hash prevents collisions

3. **Directory Creation Safety** (orchestrator.py:105-106)
   ```python
   directory.mkdir(parents=True, exist_ok=True)
   ```
   - Safe recursive creation
   - No race condition with exist_ok=True

4. **Filename Validation** (naming.py:60-67)
   ```python
   if len(self.property_hash) != 8:
       raise ValueError(f"property_hash must be 8 chars")
   if not 0 <= self.confidence <= 99:
       raise ValueError(f"confidence must be 0-99")
   ```
   - Strict validation of filename components
   - No path traversal characters allowed

5. **Structured Naming Convention** (naming.py:12-14)
   - Format: `{hash}_{loc}_{subj}_{conf}_{src}_{date}[_{seq}].png`
   - No user input in filenames
   - Predictable, parseable structure

#### ⚠️ MEDIUM PRIORITY (P2)

**M-4: Symlink Race Condition**

**Location:** `symlink_views.py:247-280`

**Issue:** TOCTOU race condition between existence check and symlink creation:

```python
# Line 262-263
if target.exists() or target.is_symlink():
    return False
# RACE WINDOW: attacker could create symlink here
# Line 269-271
target.symlink_to(rel_source)  # Could overwrite malicious symlink
```

**Exploitation Scenario:**
1. Attacker creates symlink at `target` pointing to `/etc/passwd`
2. Race window between check and creation
3. Code follows symlink and overwrites sensitive file

**Impact:** Overwrite of system files, privilege escalation

**Remediation:**
```python
def _create_link(self, source: Path, target: Path) -> bool:
    try:
        target.parent.mkdir(parents=True, exist_ok=True)

        # Use exclusive creation (fails if exists)
        if self._can_symlink:
            try:
                if self.use_relative_links:
                    rel_source = os.path.relpath(source, target.parent)
                    os.symlink(rel_source, target)  # Atomic, fails if exists
                else:
                    os.symlink(source.resolve(), target)
            except FileExistsError:
                return False  # Already exists, skip
        else:
            # Atomic copy on Windows
            shutil.copy2(source, target)

        return True

    except (OSError, PermissionError) as e:
        logger.debug(f"Failed to create link {target}: {e}")
        return False
```

**Risk Score:** MEDIUM (requires local file system access + race timing)

---

**M-5: Windows Junction Security**

**Location:** `symlink_views.py:74-102`

**Issue:** On Windows without admin rights, the code falls back to file copies instead of junctions. The detection logic could be more robust.

**Remediation:**
```python
def _check_symlink_capability(self) -> bool:
    """Check if symlinks are supported with security validation."""
    if os.name == "nt":
        import ctypes
        # Check for SeCreateSymbolicLinkPrivilege
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
        except Exception:
            pass

        # Test with actual symlink creation
        test_dir = self.views_dir / ".symlink_test"
        test_link = self.views_dir / ".symlink_test_link"
        try:
            test_dir.mkdir(parents=True, exist_ok=True)

            # Verify no existing link/junction
            if test_link.exists() or test_link.is_symlink():
                test_link.unlink()

            # Try directory junction (works without admin)
            import subprocess
            subprocess.run(
                ['mklink', '/J', str(test_link), str(test_dir)],
                shell=True,
                check=True,
                capture_output=True
            )
            test_link.unlink()
            test_dir.rmdir()
            return True
        except Exception:
            logger.warning("Symlinks/junctions not available. Using copies.")
            if test_dir.exists():
                test_dir.rmdir()
            return False
    return True
```

**Risk Score:** MEDIUM (degrades to less efficient copies on Windows)

---

#### ✅ LOW PRIORITY (P3)

**L-1: Relative Path Symlinks**

**Location:** `symlink_views.py:267-269`

**Issue:** Relative symlinks could break if directory structure changes, but this is by design for portability.

**Recommendation:** Document symlink behavior in code comments. No code change needed.

---
