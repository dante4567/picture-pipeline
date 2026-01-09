# Metadata Strategy: Best of All Worlds

**CRITICAL RULE**: Original files are **NEVER** modified. Only XMP sidecars and database entries.

---

## Philosophy: Three-Layer Metadata

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: ORIGINALS (READ-ONLY, NEVER TOUCHED)          │
│   - icloudpd: GPS Date/Time stamps (legal proof)       │
│   - iphoneSync: HDR/AF camera data                     │
│   - Files stored on NAS with original EXIF intact      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: XMP SIDECARS (MERGED METADATA)                │
│   - picture-pipeline writes merged metadata to .xmp     │
│   - GPS Date/Time from icloudpd (if available)         │
│   - HDR/AF data from iphoneSync (if available)         │
│   - Face recognition results                            │
│   - Aesthetic scores                                    │
│   - life-log event links                                │
│   - Tool-agnostic (works with digiKam, PhotoPrism)     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3: DATABASE (SEARCHABLE, QUERYABLE)              │
│   - PostgreSQL with merged metadata from all sources   │
│   - pgvector for embeddings                             │
│   - Fast queries, timeline views                        │
│   - life-log event reconstruction                       │
└─────────────────────────────────────────────────────────┘
```

---

## GPS = iPhone Verification

### Question: "Is GPS enough to say it's from iPhone?"

**Answer**: YES, if combined with other EXIF tags.

Your photos have:
- ✅ Camera Make: Apple
- ✅ Camera Model: iPhone 8 / iPhone 14 Pro
- ✅ iOS Version: 11.3 / 16.4.1
- ✅ GPS Coordinates: 51.0, 7.0
- ✅ GPS Accuracy: 4.66m
- ✅ Content Identifier (Apple UUID)
- ✅ Live Photo metadata

**This combination = 80-100% confidence iPhone photo.**

**GPS alone is NOT enough** (could be any GPS-enabled camera), but **GPS + Apple Make + iPhone Model = definitive proof**.

---

## icloudpd GitHub Findings

**Sources:**
- [icloud_photos_downloader GitHub](https://github.com/icloud-photos-downloader/icloud_photos_downloader)
- [Issue #448: Write EXIF information from Apple metadata](https://github.com/icloud-photos-downloader/icloud_photos_downloader/issues/448)

### Key Findings from GitHub:

1. **XMP Sidecar Support** (Added January 2025, v1.25.0):
   - icloudpd now exports Apple Photos metadata to XMP sidecars
   - Includes: GPS location, keywords, persons (faces), albums
   - Works with Lightroom, digiKam, PhotoPrism

2. **`--set-exif-datetime` Option**:
   - Updates EXIF timestamps for photos
   - Preserves original capture date/time

3. **Metadata Preservation**:
   - GPS coordinates: ✅ Preserved in downloaded files
   - Timestamps: ✅ Preserved with `--set-exif-datetime`
   - Keywords/Albums: ✅ Available via XMP sidecars
   - Faces: ✅ Available via XMP sidecars

### Your icloudpd Setup

Based on your directory structure and metadata analysis, you're running icloudpd with options like:
```bash
icloudpd \
  --directory /mnt/nas-photos/02-renamed-heic-from-icloudp-of-pics-i-took/ \
  --folder-structure {:%Y}/{:%Y-%m-%d} \
  --set-exif-datetime \
  --live-photo-size original
```

**Result**: Your icloudpd photos have **GPS Date/Time stamps** that iphoneSync strips.

---

## Complete Photo Inventory

| Source | Photos | Storage | Date Range | GPS Temporal Metadata |
|--------|--------|---------|------------|----------------------|
| **icloudpd** | 51,187 | 83 GB | 2017-2025 | ✅ **GPS Date/Time** (CRITICAL!) |
| **iphoneSync** | 61,323 | ~105 GB* | 2023-2025 | ❌ Stripped, has HDR/AF |
| **myPicturesFromMyIphone** | 23,543 | ~40 GB* | 2023-2025 | ❓ Need to check |
| **TOTAL** | 136,053 | ~228 GB | | |

*Estimated, awaiting du results

---

## Metadata Merge Strategy

### For Photos in BOTH icloudpd AND iphoneSync:

**Step 1: Identify duplicates** (SHA256 hash matching):
```python
# Same photo in both sources
icloudpd_photo = "2023-04-09T11-53-25_iPhone14Pro_1a3410e9.heic"
iphoneSync_photo = "2023-04-09T11-53-25_iPhone14Pro_1a3410e9.heic"

if sha256(icloudpd_photo) == sha256(iphoneSync_photo):
    # MERGE metadata from both
```

**Step 2: Extract metadata from BOTH sources**:
```python
icloudpd_exif = extract_exif(icloudpd_photo)  # Has GPS Date/Time
iphoneSync_exif = extract_exif(iphoneSync_photo)  # Has HDR/AF
```

**Step 3: Merge to XMP sidecar** (best of all worlds):
```xml
<!-- merged.xmp -->
<x:xmpmeta>
  <!-- From icloudpd (PRIORITY for GPS temporal) -->
  <exif:GPSLatitude>51.0</exif:GPSLatitude>
  <exif:GPSLongitude>7.0</exif:GPSLongitude>
  <exif:GPSDateStamp>2023:04:09</exif:GPSDateStamp>  <!-- CRITICAL! -->
  <exif:GPSTimeStamp>11:53:25</exif:GPSTimeStamp>    <!-- CRITICAL! -->
  <custom:GPSAccuracy>4.66m</custom:GPSAccuracy>
  <custom:SourceQuality>icloudpd-primary</custom:SourceQuality>

  <!-- From iphoneSync (PRIORITY for camera processing) -->
  <custom:HDRHeadroom>0.991</custom:HDRHeadroom>
  <custom:HDRGain>0.005</custom:HDRGain>
  <custom:AFConfidence>high</custom:AFConfidence>
  <custom:AFMeasuredDepth>present</custom:AFMeasuredDepth>

  <!-- From BOTH (for verification) -->
  <custom:ContentIdentifierIcloud>A61BB03B-A8C9-435F-9578-10F8CBBF214E</custom:ContentIdentifierIcloud>
  <custom:ContentIdentifierSync>75820DE3-D5DC-41E9-B218-94A1A0458986</custom:ContentIdentifierSync>

  <!-- Added by picture-pipeline -->
  <custom:iPhoneVerified>true</custom:iPhoneVerified>
  <custom:VerificationConfidence>1.0</custom:VerificationConfidence>
  <custom:iPhoneModel>iPhone 14 Pro</custom:iPhoneModel>
  <custom:iOSVersion>16.4.1</custom:iOSVersion>
  <custom:ImportedFrom>icloudpd+iphoneSync</custom:ImportedFrom>
  <custom:ImportDate>2026-01-09T02:30:00Z</custom:ImportDate>
</x:xmpmeta>
```

**Step 4: Store in database**:
```sql
INSERT INTO photos.images (
  sha256_hash,
  is_iphone_photo,
  iphone_model,
  gps_latitude,
  gps_longitude,
  gps_date_time,        -- FROM ICLOUDPD (critical!)
  gps_accuracy,
  hdr_headroom,         -- FROM IPHONESYNC
  hdr_gain,             -- FROM IPHONESYNC
  date_taken,
  file_path,
  xmp_path,
  metadata              -- JSONB with full merged metadata
) VALUES (
  '75820de3d5dc41e9b21894a1a0458986',
  true,
  'iPhone 14 Pro',
  51.0,
  7.0,
  '2023-04-09 11:53:25+02',  -- GPS-recorded time (legal proof!)
  4.66,
  0.991,
  0.005,
  '2023-04-09 11:53:25',
  '/mnt/nas/photos/originals/2023/04/09/75820de3.heic',
  '/mnt/nas/photos/originals/2023/04/09/75820de3.xmp',
  '{"sources": ["icloudpd", "iphoneSync"], ...}'
);
```

---

## Safety Guarantees

### 1. Originals NEVER Modified

```python
# picture-pipeline NEVER writes to original files
def import_photo(source_path: Path, dest_path: Path):
    # Copy (don't move) original
    shutil.copy2(source_path, dest_path)

    # Make original READ-ONLY
    dest_path.chmod(0o444)  # r--r--r--

    # Write metadata to XMP sidecar ONLY
    xmp_path = dest_path.with_suffix('.xmp')
    write_xmp_sidecar(xmp_path, merged_metadata)

    # Store in database
    store_in_database(merged_metadata)
```

**Result**: Original files remain bit-for-bit identical to source.

### 2. XMP Sidecars for Tool Compatibility

XMP sidecars work with:
- ✅ digiKam (reads and writes XMP)
- ✅ PhotoPrism (reads XMP)
- ✅ Lightroom (reads and writes XMP)
- ✅ Darktable (reads XMP)
- ✅ Any tool supporting XMP standard

**Benefit**: Tools can enrich metadata (tags, faces, albums) and picture-pipeline re-imports.

### 3. Database for Fast Queries

PostgreSQL database enables:
- Fast timeline queries: "Show photos from 2023-04-09"
- Location queries: "Photos taken in Germany"
- life-log reconstruction: "What did I do on this day?"
- Face search: "Photos with daughter"
- Duplicate detection: SHA256 queries

---

## Import Priority (Updated)

### Phase 1: icloudpd (GPS Temporal Foundation)

```bash
./run.sh import \
  --source /mnt/nas-photos/02-renamed-heic-from-icloudp-of-pics-i-took/ \
  --verify-iphone \
  --preserve-gps-temporal \
  --mark-as-primary
```

**Why first**: GPS Date/Time stamps are **irreplaceable legal proof**.

### Phase 2: iphoneSync (Fill Gaps + HDR Data)

```bash
./run.sh import \
  --source /mnt/nas-photos/02-renamed-heic-from-iphoneSync-of-pics-i-took/ \
  --skip-duplicates \
  --merge-metadata-with-icloudpd \
  --preserve-hdr
```

**For duplicates**: Merge HDR/AF data from iphoneSync into icloudpd's XMP sidecar.
**For unique photos**: Import as new (10,136 additional photos).

### Phase 3: myPicturesFromMyIphone (Manual Subset?)

```bash
./run.sh import \
  --source /mnt/nas-photos/myPicturesFromMyIphone/ \
  --skip-duplicates \
  --check-if-subset
```

**Check**: Are these 23,543 photos already in icloudpd/iphoneSync?

---

## Verification Strategy

### After Import, Verify Completeness:

```bash
# Verify all icloudpd photos imported
./run.sh verify-import --source icloudpd
# Expected: 51,187/51,187 photos verified

# Verify iphoneSync photos (unique + merged)
./run.sh verify-import --source iphoneSync
# Expected: 61,323/61,323 (10,136 unique + 51,187 merged)

# Check for missing photos
./run.sh report --missing-photos
# Expected: 0 missing

# Verify GPS Date/Time preservation
./run.sh verify-metadata --check gps-temporal
# Expected: All icloudpd photos have GPS Date/Time stamps
```

---

## life-log Integration

### GPS Temporal Metadata = Legal Proof

For life-log/diary reconstruction, GPS temporal metadata is **CRITICAL**:

**Example query**:
```sql
SELECT
  gps_latitude,
  gps_longitude,
  gps_date_time,     -- GPS-recorded time (not EXIF Date/Time!)
  gps_accuracy,
  iphone_model
FROM photos.images
WHERE date_taken::date = '2023-04-09'
  AND is_iphone_photo = true
ORDER BY gps_date_time;
```

**Result**:
```
51.0, 7.0, 2023-04-09 11:53:25+02, 4.66m, iPhone 14 Pro
```

**This proves**: "I was at 51.0, 7.0 at 11:53:25 on 2023-04-09, verified by iPhone GPS."

**Legal weight**: GPS timestamp is independent of system clock, harder to fake.

---

## Summary

### ✅ Your Strategy is Correct

1. **icloudpd preserves GPS Date/Time** → Use as primary source
2. **iphoneSync has more photos** → Fill gaps, merge HDR metadata
3. **XMP sidecars = tool-agnostic** → Works with all photo apps
4. **Database = fast queries** → life-log reconstruction
5. **Originals NEVER modified** → Safe, reversible

### 📊 Expected Results

**Before consolidation**:
- 136,053 photos across 3 sources
- ~228 GB with duplicates
- Metadata fragmented

**After consolidation**:
- ~65,000-70,000 unique photos (after deduplication)
- ~130 GB originals (NAS warm tier)
- ~15 GB thumbnails (local hot tier)
- GPS Date/Time stamps preserved for icloudpd photos
- HDR/AF metadata merged for all photos
- XMP sidecars with "best of all worlds"

**Storage savings**: ~40-50% (~98 GB freed)

**life-log benefit**: GPS-verified location timeline for iPhone photos.

---

*Next: Implement metadata merger and SHA256 deduplication*
