# Consolidation Strategy: From Chaos to Order

Dealing with photos scattered across multiple systems.

---

## Your Current Situation

**You've tried multiple systems** and now photos are everywhere:

### Cloud/Network Software
- ✅ **Immich** - Some photos indexed
- ✅ **Damselfly** - Different set indexed
- ✅ **PhotoPrism** - Another index
- ✅ **iCloud Photos** - iPhone backups
- ✅ **Google Photos** (Android Photos) - Another cloud backup

### Local Apps
- ✅ **digiKam** - Desktop organization
- ✅ **Photos app** (Mac) - Local library
- ✅ **Windows Photos** - If you have Windows machines

**Result**: CHAOS 🔥
- Photos duplicated 3-5x across systems
- Same photo indexed by multiple tools
- Different metadata in each tool
- Don't know which version is "master"
- Can't delete anything without fear
- Wasted storage (TBs of duplicates)

---

## The Problem

### Why Multiple Tools Failed

Each tool tried to be "the one":
- Immich wanted its own storage structure
- PhotoPrism wanted to index everything
- digiKam wanted its own database
- iCloud Photos kept everything in cloud
- Google Photos has its own copy

**None of them talked to each other.**

### Data Fragmentation

```
iCloud Photos (Cloud)
  ├── 20,000 iPhone photos
  └── Original HEIC format

Google Photos (Android backup)
  ├── 15,000 photos (some duplicates)
  └── Compressed JPG

Immich (Self-hosted)
  ├── 25,000 photos (tried to migrate from iCloud)
  ├── Own database
  └── Own storage structure

PhotoPrism (Self-hosted)
  ├── 18,000 photos (tried to scan existing)
  ├── Own database
  └── Own thumbnails

Damselfly (Tried briefly)
  ├── 10,000 photos scanned
  └── Own database

digiKam (Desktop)
  ├── 30,000 photos (longest used)
  ├── Albums and tags
  └── Original files + XMP

NAS (Various folders)
  ├── /Photos/2020/
  ├── /Pictures/iPhone/
  ├── /Backup/Photos/
  └── /Old_Computer/Pictures/
```

**Estimated duplicates**: 40-60% 😱

---

## picture-pipeline Solution: Consolidation Layer

### New Architecture

```
┌────────────────────────────────────────────────────────┐
│ picture-pipeline (CONSOLIDATION LAYER)                 │
│                                                          │
│ 1. Import from ALL sources                             │
│ 2. Deduplicate (SHA256 + perceptual)                   │
│ 3. Verify iPhone photos (GPS proof)                    │
│ 4. Centralized storage (NAS organized by date)         │
│ 5. XMP sidecars (universal metadata)                   │
│ 6. Export to life-log (diary events)                   │
│                                                          │
│ Result: Single source of truth                         │
│         /mnt/nas/photos/originals/                     │
└────────────────────────────────────────────────────────┘
                          ↓
            All tools point HERE (read-only)
```

---

## Phase 1: Discovery & Inventory

### Find All Photo Locations

```bash
# Create inventory of all photo sources
./run.sh inventory

# This will scan:
# 1. iCloud Photos (~/Library/Mobile Documents/...)
# 2. digiKam library (from config)
# 3. NAS directories
# 4. External drives
# 5. Immich storage (if accessible)
# 6. PhotoPrism storage
# 7. Damselfly storage
```

**Output**: `inventory.json`
```json
{
  "sources": [
    {
      "name": "iCloud Photos",
      "path": "~/Pictures/iCloud Photos",
      "count": 20000,
      "size_gb": 150,
      "formats": {"HEIC": 18000, "JPG": 2000}
    },
    {
      "name": "digiKam Library",
      "path": "/mnt/nas/Photos/digikam",
      "count": 30000,
      "size_gb": 500,
      "formats": {"JPG": 25000, "RAW": 5000}
    },
    {
      "name": "Immich Storage",
      "path": "/mnt/nas/immich/library",
      "count": 25000,
      "size_gb": 300,
      "estimated_duplicates": 15000
    }
  ],
  "total_photos": 75000,
  "estimated_unique": 35000,
  "estimated_duplicates": 40000,
  "total_size_gb": 950,
  "estimated_after_dedup_gb": 450
}
```

---

## Phase 2: Deduplication Analysis

### Find Duplicates BEFORE Import

```bash
# Scan all sources, find duplicates
./run.sh deduplicate --dry-run

# This calculates:
# 1. SHA256 hash for each photo
# 2. Perceptual hash (for edited versions)
# 3. Groups duplicates
# 4. Shows which source has "best" version
```

**Output**: `duplicates.json`
```json
{
  "duplicate_groups": [
    {
      "group_id": 1,
      "sha256": "abc123...",
      "photos": [
        {
          "path": "~/Pictures/iCloud Photos/IMG_1234.HEIC",
          "source": "iCloud",
          "format": "HEIC",
          "size_bytes": 4500000,
          "is_iphone_photo": true,
          "has_gps": true,
          "quality_score": 10  // Original, highest quality
        },
        {
          "path": "/mnt/nas/immich/library/2024/06/abc123.jpg",
          "source": "Immich",
          "format": "JPG",
          "size_bytes": 3200000,
          "is_iphone_photo": true,
          "has_gps": true,
          "quality_score": 8  // Converted from HEIC
        },
        {
          "path": "/mnt/nas/Photos/2024/IMG_1234.JPG",
          "source": "digiKam",
          "format": "JPG",
          "size_bytes": 2800000,
          "is_iphone_photo": false,  // Lost metadata
          "has_gps": false,
          "quality_score": 6  // Further compressed
        }
      ],
      "recommendation": "Keep iCloud version (best quality, full metadata)"
    }
  ]
}
```

---

## Phase 3: Smart Import Strategy

### Prioritized Import Order

```python
# Import strategy (highest priority first)
IMPORT_PRIORITY = [
    {
        "source": "iCloud Photos",
        "reason": "Original iPhone photos with full metadata",
        "action": "Import all, mark as iPhone verified"
    },
    {
        "source": "digiKam Library",
        "reason": "Has albums, tags, edits (XMP sidecars)",
        "action": "Import unique photos + all XMP metadata"
    },
    {
        "source": "Immich Storage",
        "reason": "May have photos not in iCloud",
        "action": "Import only non-duplicates"
    },
    {
        "source": "PhotoPrism Storage",
        "reason": "Likely all duplicates",
        "action": "Skip duplicates, import only unique"
    },
    {
        "source": "Damselfly Storage",
        "reason": "Tried briefly, likely all duplicates",
        "action": "Skip duplicates, verify completeness"
    },
    {
        "source": "Google Photos",
        "reason": "Android backups, may have unique photos",
        "action": "Export from Google, import non-duplicates"
    }
]
```

### Import Process

```bash
# 1. Import iCloud (highest quality, iPhone verification)
./run.sh import --source icloud --verify-iphone

# 2. Import digiKam (albums, tags, edits)
./run.sh import --source digikam --preserve-xmp --skip-duplicates

# 3. Import Immich (check for unique)
./run.sh import --source immich --skip-duplicates

# 4. Import PhotoPrism (likely all duplicates)
./run.sh import --source photoprism --skip-duplicates

# 5. Import Google Photos (export first)
./run.sh import --source google-photos-export --skip-duplicates
```

---

## Phase 4: Metadata Consolidation

### Merge Metadata from All Sources

Example: Same photo has different metadata in different tools

**iCloud Photos**:
- GPS: 47.606200, -122.332100
- Date: 2024:06:15 10:23:45
- Model: iPhone 14 Pro

**digiKam**:
- Tags: ["vacation", "family", "beach"]
- Album: "Summer 2024"
- Rating: 5 stars
- Edited: Yes (exposure adjustment)

**Immich**:
- Faces: ["Daughter" (confidence: 0.95)]
- Album: "Beach Trip"

**PhotoPrism**:
- Location: "Alki Beach, Seattle"
- AI Tags: ["outdoor", "water", "people"]

**picture-pipeline consolidates ALL metadata**:
```xml
<!-- consolidated.xmp -->
<x:xmpmeta>
  <!-- From iCloud (HIGHEST PRIORITY) -->
  <exif:GPSLatitude>47.606200</exif:GPSLatitude>
  <exif:GPSLongitude>-122.332100</exif:GPSLongitude>
  <custom:iPhoneVerified>true</custom:iPhoneVerified>
  <custom:iPhoneModel>iPhone 14 Pro</custom:iPhoneModel>

  <!-- From digiKam -->
  <dc:subject>
    <rdf:Bag>
      <rdf:li>vacation</rdf:li>
      <rdf:li>family</rdf:li>
      <rdf:li>beach</rdf:li>
    </rdf:Bag>
  </dc:subject>
  <xmp:Rating>5</xmp:Rating>
  <custom:Album>Summer 2024</custom:Album>
  <custom:Edited>true</custom:Edited>

  <!-- From Immich -->
  <custom:Faces>
    <rdf:li>
      <custom:PersonName>Daughter</custom:PersonName>
      <custom:Confidence>0.95</custom:Confidence>
    </rdf:li>
  </custom:Faces>

  <!-- From PhotoPrism -->
  <custom:LocationName>Alki Beach, Seattle</custom:LocationName>
  <custom:AITags>outdoor, water, people</custom:AITags>
</x:xmpmeta>
```

**Result**: Best of all tools combined!

---

## Phase 5: Tool Reconfiguration

### After Consolidation, Point All Tools to Master

```yaml
# All tools now point to picture-pipeline storage
master_storage: /mnt/nas/photos/originals/

# Immich: External library (read-only)
immich:
  mode: external_library
  path: /mnt/nas/photos/originals/
  import: false  # Don't duplicate
  scan_only: true

# PhotoPrism: Index only (read-only)
photoprism:
  mode: read_only
  path: /mnt/nas/photos/originals/
  import: false

# digiKam: Direct access (read-write for editing)
digikam:
  mode: direct
  path: /mnt/nas/photos/originals/
  database: /mnt/nas/photos/digikam.db
  write_xmp: true  # Write back to sidecars

# Damselfly: Retire (redundant with PhotoPrism)
damselfly:
  status: retired
  reason: "Redundant with PhotoPrism web UI"
```

---

## Expected Results

### Storage Savings

**Before consolidation**:
```
iCloud Photos:    150 GB
Google Photos:    120 GB (compressed duplicates)
Immich:           300 GB (many duplicates)
PhotoPrism:       200 GB (thumbnails + database)
Damselfly:        100 GB (partial scan)
digiKam:          500 GB (mix of originals + duplicates)
NAS scattered:    400 GB (old backups)
──────────────────────────
Total:           1770 GB
```

**After consolidation**:
```
picture-pipeline originals:  450 GB (unique photos only)
picture-pipeline thumbs:      15 GB (local thumbnails)
picture-pipeline sidecars:   0.5 GB (XMP metadata)
Immich database:              5 GB (metadata only)
PhotoPrism database:         10 GB (metadata only)
digiKam database:             2 GB (metadata only)
──────────────────────────
Total:                      482.5 GB
──────────────────────────
Savings:                   1287.5 GB (73% reduction!)
```

### Clarity Restored

**Before**:
- ❌ Photos scattered across 7+ locations
- ❌ Don't know which is "master"
- ❌ Duplicates everywhere
- ❌ Different metadata in each tool
- ❌ Fear of deleting anything

**After**:
- ✅ Single source of truth: `/mnt/nas/photos/originals/`
- ✅ No duplicates (SHA256 verified)
- ✅ All metadata consolidated (XMP sidecars)
- ✅ All tools work together (not against each other)
- ✅ Can safely delete tool-specific copies

---

## Implementation Timeline

### Week 1: Discovery
- [ ] Run inventory across all sources
- [ ] Document what's where
- [ ] Estimate duplicates
- [ ] Calculate storage savings

### Week 2: Deduplication Analysis
- [ ] Hash all photos (SHA256)
- [ ] Find duplicate groups
- [ ] Determine "best" version of each
- [ ] Create import plan

### Week 3: Import (Phase 1)
- [ ] Import iCloud Photos (highest priority)
- [ ] Verify iPhone photos (GPS, metadata)
- [ ] Generate thumbnails
- [ ] Write XMP sidecars

### Week 4: Import (Phase 2)
- [ ] Import digiKam library (preserve metadata)
- [ ] Import Immich unique photos
- [ ] Import PhotoPrism unique photos
- [ ] Skip all duplicates

### Week 5: Metadata Consolidation
- [ ] Merge tags from digiKam
- [ ] Merge face recognition from Immich
- [ ] Merge AI tags from PhotoPrism
- [ ] Update XMP sidecars

### Week 6: Tool Reconfiguration
- [ ] Point Immich to picture-pipeline storage
- [ ] Point PhotoPrism to picture-pipeline storage
- [ ] Point digiKam to picture-pipeline storage
- [ ] Test all tools work

### Week 7: Cleanup
- [ ] Verify all photos accessible
- [ ] Delete duplicate tool-specific copies
- [ ] Retire Damselfly (redundant)
- [ ] Backup consolidated storage

---

## Safety Measures

### Before Deleting Anything

```bash
# 1. Verify all photos imported
./run.sh verify-import --source icloud
./run.sh verify-import --source digikam
./run.sh verify-import --source immich

# 2. Generate reports
./run.sh report --missing-photos
./run.sh report --import-summary

# 3. Create backup
rsync -av /mnt/nas/photos/originals/ /backup/photos-consolidated-$(date +%Y%m%d)/

# 4. Only then delete duplicates
./run.sh cleanup --dry-run  # See what would be deleted
./run.sh cleanup --confirm  # Actually delete
```

---

## Handling Special Cases

### Google Photos Export

```bash
# 1. Export from Google Photos
# Go to takeout.google.com
# Select "Photos" only
# Download (may take days for large libraries)

# 2. Import Google Photos export
./run.sh import --source google-takeout --path ~/Downloads/takeout-photos/
# This handles Google's weird folder structure and JSON metadata
```

### digiKam Albums/Tags

```bash
# Preserve digiKam organization
./run.sh import --source digikam --preserve-albums --preserve-tags

# This creates corresponding albums in picture-pipeline
# And writes all tags to XMP sidecars
```

### Edited Photos

```bash
# digiKam edited versions
./run.sh import --source digikam --include-edited-versions

# This imports both:
# - Original: IMG_1234.JPG
# - Edited:   IMG_1234_edited.JPG
# And links them (metadata: original -> edited)
```

---

## Your Specific Situation

Based on having tried multiple tools:

1. **iCloud Photos** → Highest priority (iPhone originals)
2. **digiKam** → Second priority (your longest-used, has albums/tags)
3. **Immich** → Check for unique uploads
4. **PhotoPrism** → Likely all duplicates, but check
5. **Damselfly** → Likely can retire
6. **Google Photos** → Export and check for Android-specific photos

**Estimated timeline**: 6-7 weeks to fully consolidate

**Estimated storage savings**: 60-75% (1TB+ freed)

**Result**: One master library, all tools working together! 🎯

---

*Next: Run `./run.sh inventory` to discover all photo locations*
