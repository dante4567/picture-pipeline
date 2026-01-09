# CLAUDE.md

> Instructions for Claude Code when working with picture-pipeline

---

## 📚 Modular Reference & Commands

**Load task-specific guidance only when needed:**

| When Working On | Read This |
|-----------------|-----------|
| **API endpoints, routes, schemas** | `.claude/reference/python-api-development.md` |
| **Docker, deployment** | `.claude/reference/docker-deployment.md` |
| **Writing tests** | `.claude/reference/testing-patterns.md` |
| **Security, auth** | `.claude/reference/security-practices.md` |

**Automate repetitive tasks:**
- `/add-test` - Generate test suite
- `/refactor` - Refactor code following best practices
- `/security-check` - Audit for OWASP Top 10

---

## Quick Context

**Project:** picture-pipeline
**Purpose:** Centralized photo management - source of truth for all photo tools
**Current version:** v1.0.0
**Current focus:** iPhone photo verification (HIGHEST PRIORITY)

---

## Why picture-pipeline is Critical

This is **THE FOUNDATION** for life-log/diary because:

1. **iPhone photos = ground truth**: Prove "I was at X location at Y time"
2. **Legal/personal proof**: GPS + timestamp + verified iPhone metadata
3. **Reverse-engineered diary**: "What did I do on 2024-06-15?" → Automated
4. **Family tracking**: "What did daughter do on X day, with whom?"
5. **Dawarich integration**: Verified location timeline

**Without this, life-log is just speculation. With this, it's factual.**

---

## Priority Implementation Order

### Phase 1: iPhone Verification (CURRENT) ✅
- ✅ ExifTool integration
- ✅ Metadata extraction
- ✅ iPhone detection (make, model, iOS)
- ✅ GPS extraction
- ✅ Confidence scoring
- ⏳ **NEXT**: Test with real iPhone photos

### Phase 2: Storage & Deduplication
- SHA256 hashing
- Perceptual hashing
- Storage tier management
- Thumbnail generation

### Phase 3: Face Recognition
- Family training (daughter, spouse)
- 95%+ confidence matching
- XMP sidecar writing

### Phase 4: Integration
- life-log event export
- Dawarich location export
- Tool integration (Immich, digiKam)

---

## iPhone Verification: How It Works

```python
from src.metadata.iphone_verifier import iPhonePhotoVerifier

verifier = iPhonePhotoVerifier()
result = verifier.verify_iphone_photo(Path("photo.jpg"))

if result.is_iphone_photo:
    print(f"✓ Verified iPhone photo: {result.iphone_model}")
    print(f"  Confidence: {result.confidence:.1%}")
    if result.has_gps:
        print(f"  Location: {result.gps_latitude}, {result.gps_longitude}")
        print(f"  Accuracy: {result.gps_accuracy}m")
else:
    print(f"✗ Not an iPhone photo (confidence: {result.confidence:.1%})")
```

**Verification checks:**
1. Camera make = "Apple" (required)
2. Camera model starts with "iPhone" (required)
3. Software contains "iOS" (highly recommended)
4. Apple-specific EXIF tags present (strong indicator)
5. GPS data extracted (critical for life-log)

**Confidence scoring:**
- 1.0 = Definite iPhone photo (all checks pass)
- 0.7-0.9 = Likely iPhone photo (most checks pass)
- <0.7 = Not verified as iPhone

---

## Testing

### Unit Tests
```bash
./run.sh test
```

### Test with Real iPhone Photo
```bash
./run.sh verify-iphone /path/to/iphone/photo.jpg
```

**Expected output:**
```
Is iPhone Photo: ✓ YES
Confidence: 100.0%
Model: iPhone 14 Pro
iOS: iOS 17.2

GPS: 47.606200, -122.332100
GPS Accuracy: 8.5m
Date Taken: 2024:06:15 10:23:45

HDR: Yes
Live Photo: Yes

Verification Details:
  ✓ Camera make: Apple
  ✓ Camera model: iPhone 14 Pro
  ✓ iOS software: iOS 17.2
  ✓ Apple tags: Apple:ContentIdentifier, Apple:ImageUniqueID
  ✓ GPS data present (accuracy: 8.5m)
  ✓ HDR photo
  ✓ Live Photo
```

---

## Dependencies

### System Requirements
- **ExifTool**: `sudo apt install libimage-exiftool-perl`
- **Python 3.11+**

### Python Packages
```bash
pip install -r requirements.txt
```

**Key packages:**
- Pillow - Image processing
- pillow-heif - HEIC support
- imagehash - Perceptual hashing
- face-recognition - Face detection
- litellm - AI/LLM integration
- sqlalchemy + pgvector - Database

---

## Storage Architecture

### Tier Structure

```
Hot (NVMe SSD - Local)
  ~/.local/share/pictures/
    thumbs/tiny/    # 150x150
    thumbs/small/   # 500x500
    thumbs/medium/  # 1920x1080
    cache/full/     # Recently accessed originals
    screenshots/    # Organized, renamed

Warm (HDD - NAS)
  /mnt/nas/photos/active/
    YYYY/MM/DD/<hash>.jpg      # Easily-used formats (JPG, H.264)
    YYYY/MM/DD/<hash>.xmp      # Sidecars

Cold (Archive)
  /mnt/nas/photos/archive/
    YYYY/<hash>.heic            # Original formats
    YYYY/<hash>.hevc
```

---

## Database Schema

```sql
CREATE SCHEMA photos;

CREATE TABLE photos.images (
    id SERIAL PRIMARY KEY,
    sha256_hash VARCHAR(64) UNIQUE NOT NULL,
    perceptual_hash VARCHAR(64) NOT NULL,

    -- iPhone verification (CRITICAL)
    is_iphone_photo BOOLEAN DEFAULT FALSE,
    iphone_model VARCHAR(100),
    iphone_ios_version VARCHAR(50),

    -- Location (for Dawarich + life-log)
    gps_latitude FLOAT,
    gps_longitude FLOAT,
    gps_accuracy FLOAT,

    -- Timestamps
    date_taken TIMESTAMPTZ,

    -- Storage
    file_path TEXT NOT NULL,
    storage_tier VARCHAR(10),  -- 'hot', 'warm', 'cold'

    -- AI enrichment
    aesthetic_score FLOAT,
    scene_description TEXT,

    -- Metadata
    metadata JSONB,
    xmp_path TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Critical Rules

1. **iPhone verification is HIGHEST PRIORITY** - This enables life-log
2. **Test with real iPhone photos** - Don't assume it works
3. **Preserve all metadata** - Never destructive
4. **XMP sidecars = tool-agnostic** - Works with all photo apps
5. **Storage tiers = performance + cost** - Thumbnails local, originals NAS

---

## Entry Point

```bash
./run.sh setup              # Install dependencies, check ExifTool
./run.sh verify-iphone      # Test iPhone verification
./run.sh test               # Run tests
```

---

## Documentation

- [README.md](README.md) - Project overview
- [docs/PICTURE-PIPELINE-ARCHITECTURE.md](docs/PICTURE-PIPELINE-ARCHITECTURE.md) - Complete system
- [docs/SYNC-STRATEGY.md](docs/SYNC-STRATEGY.md) - Sync consolidation
- [docs/LIFE-LOG-INTEGRATION.md](docs/LIFE-LOG-INTEGRATION.md) - Diary reconstruction
- [docs/STORAGE-TIERS.md](docs/STORAGE-TIERS.md) - Storage optimization

---

*See README.md for project overview*
*iPhone verification is the foundation - get this right first*
