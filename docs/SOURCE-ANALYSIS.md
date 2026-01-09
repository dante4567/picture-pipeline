# Photo Source Analysis

Analysis of existing photo sources on NAS to determine consolidation strategy.

---

## Timeline of Photo Organization Attempts

### June 2025 - First Attempts

| Directory | Created | Owner | Status |
|-----------|---------|-------|--------|
| `inbox` | 2025-06-14 | User 1029 (Synology) | Inactive |
| `photos` | 2025-06-14 | danielt | Empty |
| `myPicturesFromMyIphone` | 2025-06-15 | danielt | Organized by year (2023-2025) |
| `02-renamed-jpeg-from-iphoneSync-of-pics-i-took` | 2025-06-17 | User 1029 | Format-specific split |
| `02-renamed-xml-from-iphoneSync-of-pics-i-took` | 2025-06-17 | root | Format-specific split |
| `02-renamed-xmp-from-iphoneSync-of-pics-i-took` | 2025-06-18 | root | Format-specific split |

**Initial approach**: Split iphoneSync exports by file format (JPEG, XML, XMP in separate directories).

### October 31, 2025 - Major Reorganization

| Directory | Created | Owner | Photos | Status |
|-----------|---------|-------|--------|--------|
| `02-renamed-heic-from-icloudp-of-pics-i-took` | 2025-10-31 | User 1029 | **51,187** | **Active** |
| `02-renamed-heic-from-iphoneSync-of-pics-i-took` | 2025-10-31 | User 1029 | **61,323** | **Active** |

**Consolidated approach**: Single directory per sync method with organized YYYY/MM/DD structure.

---

## Current Photo Sources

### 1. icloudpd (iCloud Photos Docker Backup)

**Path**: `/mnt/nas-photos/02-renamed-heic-from-icloudp-of-pics-i-took/`
**Photos**: **51,187 files**
**Date range**: 2017 - 2025
**Format**: HEIC (primary), organized by `YYYY/YYYY-MM-DD/`
**Filename pattern**: `2018-05-08T19-37-39_iPhone8_dbf5e076.heic`

**Sample verification** (iPhone 8, 2018):
```
✓ iPhone Photo: YES
✓ Confidence: 80%
✓ Model: iPhone 8
✓ iOS: 11.3
✓ GPS: 20.0, 57.0
⚠ GPS Accuracy: 2375m (poor)
⚠ No Apple-specific tags
```

**Pros**:
- Oldest photos available (goes back to 2017)
- iCloud Photos is Apple's official backup
- Organized by date
- Docker container = automated sync

**Cons**:
- **10,136 fewer photos than iphoneSync**
- Older GPS accuracy is poor
- Missing Apple-specific EXIF tags

---

### 2. iphoneSync (iOS Photos App Sync)

**Path**: `/mnt/nas-photos/02-renamed-heic-from-iphoneSync-of-pics-i-took/`
**Photos**: **61,323 files** ← **10,136 MORE than icloudpd**
**Date range**: 2023 - 2025 (more recent)
**Format**: HEIC (primary), organized by `YYYY/YYYY-MM-DD/`
**Filename pattern**: `2023-04-09T11-53-25_iPhone14Pro_1a3410e9.heic`

**Sample verification** (iPhone 14 Pro, 2023):
```
✓ iPhone Photo: YES
✓ Confidence: 80%
✓ Model: iPhone 14 Pro
✓ iOS: 16.4.1
✓ GPS: 51.0, 7.0
✓ GPS Accuracy: 4.66m (excellent!)
⚠ No Apple-specific tags
```

**Pros**:
- **Most complete** (61,323 photos vs 51,187)
- Better GPS accuracy on newer photos (4.66m vs 2375m)
- More recent iPhone models (iPhone 14 Pro/Max)
- Same date-organized structure

**Cons**:
- May not go back as far as icloudpd (need to check oldest photo)
- Still missing Apple-specific EXIF tags (likely stripped during sync)

---

### 3. myPicturesFromMyIphone

**Path**: `/mnt/nas-photos/myPicturesFromMyIphone/`
**Owner**: danielt
**Structure**: `2023/`, `2024/`, `2025/` subdirectories
**Status**: Running analysis...

---

## Metadata Comparison (CRITICAL for life-log)

### Metadata Tag Count

| Source | Total Tags | Unique to Source |
|--------|-----------|------------------|
| **icloudpd** | 154 tags | 8 tags |
| **iphoneSync** | 169 tags | 23 tags |

### icloudpd-Specific Metadata (CRITICAL!)

Tags preserved by icloudpd but **STRIPPED by iphoneSync**:

| Tag | Value | Importance |
|-----|-------|------------|
| **GPS Date Stamp** | ✓ Present | **CRITICAL** for life-log |
| **GPS Date/Time** | ✓ Present | **CRITICAL** - Proves exact GPS timestamp |
| **GPS Time Stamp** | ✓ Present | **CRITICAL** - Independent time verification |
| OIS Mode | ✓ Present | Camera feature indicator |
| Scene Capture Type | ✓ Present | Photo type metadata |
| Flashpix Version | ✓ Present | Format version |
| Y Cb Cr Positioning | ✓ Present | Color space data |
| Components Configuration | ✓ Present | Channel configuration |

**Why GPS temporal metadata matters**:
- **Legal proof**: GPS coordinates + independent GPS timestamp = irrefutable location proof
- **life-log reconstruction**: Can verify "I was at X location at Y time" with GPS-recorded time
- **Tamper detection**: GPS time vs EXIF time mismatch = possible manipulation

### iphoneSync-Specific Metadata

Tags preserved by iphoneSync but **MISSING in icloudpd**:

| Tag | Value | Importance |
|-----|-------|------------|
| **HDR Headroom** | 0.991 | HDR processing data |
| **HDR Gain** | 0.005 | HDR enhancement value |
| **AF Confidence** | ✓ Present | Autofocus quality |
| **AF Measured Depth** | ✓ Present | Depth sensing data |
| **AF Performance** | ✓ Present | Focus accuracy |
| **Focus Position** | ✓ Present | Lens position |
| Camera Type | ✓ Present | Device identifier |
| Color Temperature | ✓ Present | White balance data |
| Composite Image | ✓ Present | Multi-frame indicator |
| Offset Time | ✓ Present | Timezone offset |

**Why camera processing metadata matters**:
- HDR detection (multi-frame photos)
- Depth/portrait mode detection
- Photo quality assessment

### Recommendation: MERGE BOTH SOURCES

**User's intuition was correct**: icloudpd DOES preserve more critical metadata for life-log purposes.

**Optimal strategy**:
1. **icloudpd = Primary for GPS temporal proof** (has GPS Date/Time stamps)
2. **iphoneSync = Fill gaps** (has 10,136 additional photos + HDR data)
3. **Merge metadata** where both have same photo (SHA256 match):
   - Take GPS Date/Time from icloudpd (critical!)
   - Take HDR/AF data from iphoneSync (nice to have)
   - Keep both Content Identifiers (different UUIDs)

---

## Photo Count Summary

| Source | Photos | Missing from others | Date Range | GPS Quality |
|--------|--------|---------------------|------------|-------------|
| **iphoneSync** | **61,323** | **+10,136** | 2023-2025 | ✓ Excellent (4.66m) |
| **icloudpd** | **51,187** | ? | 2017-2025 | ⚠ Variable (2375m old, better new) |
| **myPicturesFromMyIphone** | ??? | ??? | 2023-2025 | ??? |

---

## Key Findings

### 1. iphoneSync has MORE photos

Contrary to initial belief that "icloudSync scored highest", **iphoneSync actually has 10,136 MORE photos** than icloudpd:
- iphoneSync: 61,323 photos
- icloudpd: 51,187 photos
- **Difference: +10,136 photos (19.8% more)**

### 2. Both have good iPhone verification

Both sources pass iPhone verification with 80% confidence:
- ✓ Camera make: Apple
- ✓ Camera model detected (iPhone 8, iPhone 14 Pro)
- ✓ iOS version detected (11.3, 16.4.1)
- ✓ GPS coordinates present

### 3. GPS accuracy varies by age

- **Older photos** (2018, iPhone 8): 2375m accuracy (poor)
- **Newer photos** (2023, iPhone 14 Pro): 4.66m accuracy (excellent)

This is expected - newer iPhones have better GPS hardware.

### 4. Missing Apple-specific tags

Both sources are **missing Apple-specific EXIF tags**:
- `Apple:ContentIdentifier`
- `Apple:ImageUniqueID`
- `Apple:MediaGroupUUID`

These tags are likely **stripped during sync** to reduce metadata size. However, the **critical metadata remains**:
- GPS coordinates
- Date/time
- Camera model
- iOS version

---

## Duplicate Analysis (Preliminary)

### Potential Overlaps

Given:
- icloudpd: 51,187 photos
- iphoneSync: 61,323 photos
- Combined: 112,510 photos

**If icloudpd is SUBSET of iphoneSync**:
- Unique photos: ~61,323 (iphoneSync is complete)
- Duplicates: ~51,187 (100% overlap)
- **Estimated deduplication**: Keep iphoneSync, archive icloudpd

**If sources have DIFFERENT photos**:
- Unique photos: up to 112,510
- Duplicates: unknown (need SHA256 hashing)
- **Estimated deduplication**: Merge both sources

**Most likely scenario**: icloudpd stopped syncing at some point, iphoneSync continued.

---

## Consolidation Strategy

### Phase 1: Inventory Analysis (CURRENT)

- [x] Discover all photo sources
- [x] Count photos per source
- [x] Test iPhone verification on samples
- [ ] Check oldest/newest photos in each source
- [ ] Determine date range gaps

### Phase 2: Deduplication Analysis

Run SHA256 hashing on both sources to find:
1. Photos in BOTH sources (duplicates)
2. Photos ONLY in icloudpd (unique to iCloud sync)
3. Photos ONLY in iphoneSync (unique to iOS sync)

```bash
# Hash all photos
./run.sh deduplicate --dry-run

# Expected output:
# - Duplicates: ~40,000-50,000 (78-98% overlap)
# - Unique to icloudpd: ~1,000-10,000
# - Unique to iphoneSync: ~10,000-20,000
```

### Phase 3: Import Priority

**Recommended import order** (subject to deduplication results):

1. **iphoneSync FIRST** (61,323 photos)
   - Most complete source
   - Better GPS accuracy on recent photos
   - Import all, mark as iPhone verified

2. **icloudpd SECOND** (51,187 photos)
   - Import ONLY non-duplicates
   - May have older photos not in iphoneSync
   - Verify date ranges don't overlap

3. **myPicturesFromMyIphone** (pending count)
   - Import ONLY non-duplicates
   - Check if this is a manual subset

### Phase 4: Consolidation

```bash
# Import iphoneSync (primary source)
./run.sh import \
  --source /mnt/nas-photos/02-renamed-heic-from-iphoneSync-of-pics-i-took/ \
  --verify-iphone \
  --storage-tier warm

# Import icloudpd (fill gaps)
./run.sh import \
  --source /mnt/nas-photos/02-renamed-heic-from-icloudp-of-pics-i-took/ \
  --skip-duplicates \
  --verify-iphone \
  --storage-tier warm

# Verify completeness
./run.sh verify-import --source iphoneSync
./run.sh verify-import --source icloudpd
```

---

## Expected Results After Consolidation

### Storage Estimate

**Before**:
```
iphoneSync:      61,323 photos (assume ~400 GB for HEIC)
icloudpd:        51,187 photos (assume ~350 GB for HEIC)
──────────────────────────────
Total:          112,510 photos (~750 GB with duplicates)
```

**After deduplication** (estimated):
```
Unique photos:   ~65,000 photos (assuming 78% duplicate rate)
Storage:         ~450 GB (originals on NAS warm tier)
Thumbnails:      ~15 GB (local hot tier)
XMP sidecars:    ~500 MB
──────────────────────────────
Total:          ~465 GB (38% savings)
```

### Benefits

- ✅ Single source of truth: `/mnt/nas/photos/originals/`
- ✅ All photos iPhone verified (legal proof of location/time)
- ✅ Organized by date (YYYY/MM/DD)
- ✅ XMP sidecars (works with all photo tools)
- ✅ No duplicates (SHA256 verified)
- ✅ Can safely archive original sync directories

---

## Next Steps

1. **Analyze oldest/newest photos** in each source
2. **Run full SHA256 deduplication** to find exact overlaps
3. **Check myPicturesFromMyIphone** count and purpose
4. **Decide import priority** based on duplicate analysis
5. **Run import with picture-pipeline**

---

*This analysis will be updated as more data becomes available.*
*Current status: Preliminary analysis complete, awaiting deduplication results.*
