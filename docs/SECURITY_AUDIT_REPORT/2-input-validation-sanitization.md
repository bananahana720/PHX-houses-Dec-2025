# 2. Input Validation & Sanitization

**Files:**
- `src/phx_home_analysis/services/image_extraction/standardizer.py`
- `src/phx_home_analysis/services/infrastructure/stealth_http_client.py`

### Findings

#### ✅ STRENGTHS

1. **Image Bomb Protection** (standardizer.py:14-22)
   ```python
   Image.MAX_IMAGE_PIXELS = 178956970  # ~15000 x 12000 pixels
   MAX_RAW_FILE_SIZE = 50 * 1024 * 1024  # 50MB
   ```
   - Prevents decompression bombs at PIL level
   - File size check BEFORE opening image
   - Defense-in-depth with both size and pixel limits

2. **Multi-Stage Size Validation** (stealth_http_client.py:236-270)
   - Checks Content-Length header before download
   - Validates actual downloaded size
   - Prevents resource exhaustion attacks

3. **Content-Type Validation** (stealth_http_client.py:115-121, 218-233)
   ```python
   ALLOWED_CONTENT_TYPES = {
       "image/jpeg", "image/png", "image/webp",
       "image/gif", "image/jpg"
   }
   ```
   - Strict allowlist of image MIME types
   - Rejects HTML, scripts, executables

4. **Format Conversion** (standardizer.py:106-147)
   - Converts all images to RGB PNG
   - Handles RGBA with alpha channel properly
   - Sanitizes palette modes and grayscale

5. **Dimension Limits** (standardizer.py:149-175)
   - Max 1024px dimension with aspect ratio preservation
   - High-quality Lanczos resampling
   - Prevents extremely large images in storage

#### 🔴 HIGH PRIORITY (P1)

**H-1: No Magic Byte Validation**

**Location:** `standardizer.py:83`, `stealth_http_client.py:256`

**Issue:** The system trusts Content-Type headers and file extensions without validating magic bytes. An attacker could send malicious content with an image Content-Type.

**Exploitation Scenario:**
```http
HTTP/1.1 200 OK
Content-Type: image/png
Content-Length: 1024

<!-- Actual content is HTML with XSS payload -->
<html><script>alert('XSS')</script></html>
```

**Impact:**
- Malicious files stored as images
- If images are served without re-validation, could lead to XSS
- Polyglot files (valid image + embedded script)

**Remediation:**
```python
# Add to standardizer.py after line 80:

MAGIC_BYTES = {
    b'\xFF\xD8\xFF': 'jpeg',
    b'\x89PNG\r\n\x1a\n': 'png',
    b'GIF87a': 'gif',
    b'GIF89a': 'gif',
    b'RIFF': 'webp',  # Must check for 'WEBP' at offset 8
}

def _validate_magic_bytes(self, image_data: bytes) -> bool:
    """Validate file starts with known image magic bytes."""
    for magic, format_name in MAGIC_BYTES.items():
        if image_data.startswith(magic):
            # Additional check for WEBP
            if format_name == 'webp':
                if len(image_data) < 12 or image_data[8:12] != b'WEBP':
                    return False
            return True
    return False

# In standardize() method before line 83:
if not self._validate_magic_bytes(image_data):
    raise ImageProcessingError(
        "Invalid image format: magic bytes do not match image type"
    )
```

**Risk Score:** HIGH (bypass of security controls, potential for malicious content storage)

---

**H-2: EXIF Metadata Not Sanitized**

**Location:** `standardizer.py:92-93`

**Issue:** PIL saves images with `optimize=True` but does not explicitly strip EXIF metadata. Some EXIF fields could contain injection payloads or privacy-sensitive data.

**Exploitation Scenario:**
```python
# Attacker embeds malicious EXIF comment
exif_comment = "'; DROP TABLE properties; --"
# Or privacy leak
exif_gps = {"GPSLatitude": 33.4484, "GPSLongitude": -112.0740}
```

**Impact:**
- Privacy leak (GPS coordinates, camera model, timestamps)
- Potential injection if EXIF displayed in UI without escaping

**Remediation:**
```python
# In standardizer.py, modify save line:
img.save(
    output,
    format=self.output_format,
    optimize=True,
    exif=b''  # Strip all EXIF data
)

# Or use PIL's getexif() to selectively preserve safe fields:
safe_exif = {}  # Only include width, height, orientation if needed
img.save(output, format=self.output_format, optimize=True, exif=safe_exif)
```

**Risk Score:** HIGH (privacy leak + potential injection)

---

#### ⚠️ MEDIUM PRIORITY (P2)

**M-3: Animated Image Handling**

**Location:** `standardizer.py:250` (detects but doesn't handle)

**Issue:** Animated GIFs/PNGs are detected but not explicitly handled. Could lead to oversized files or decompression issues.

**Remediation:**
```python
def standardize(self, image_data: bytes) -> bytes:
    # After line 83:
    if hasattr(img, 'is_animated') and img.is_animated:
        # Extract first frame only
        img.seek(0)
        img = img.copy()
    # Continue with existing logic...
```

**Risk Score:** MEDIUM (resource exhaustion via animated images)

---
