# Tool Comparison: digiKam vs Immich vs PhotoPrism

Best-of-all-worlds integration strategy.

---

## TL;DR Recommendation

**Use ALL THREE** - each excels at different things:

1. **picture-pipeline** = Source of truth (deduplication, iPhone verification, metadata)
2. **Immich** = Mobile app + sharing (best mobile experience)
3. **digiKam** = Local editing + organization (best desktop app)
4. **PhotoPrism** = Web browsing + AI (best web UI)

**All three read from the same NAS storage managed by picture-pipeline.**

---

## Tool Comparison Matrix

| Feature | digiKam | Immich | PhotoPrism | picture-pipeline |
|---------|---------|--------|------------|-------------------|
| **Platform** | Desktop (Linux/Win/Mac) | Web + Mobile app | Web only | CLI/Backend |
| **Editing** | ★★★★★ Full RAW | ★☆☆☆☆ Basic | ★★☆☆☆ Filters | ❌ Not a photo editor |
| **Mobile App** | ❌ No | ★★★★★ Excellent | ❌ No (PWA only) | ❌ No |
| **Face Recognition** | ★★★☆☆ Good | ★★★★★ Excellent | ★★★★☆ Good | ★★★★★ Custom (family-focused) |
| **AI Features** | ★★☆☆☆ Tags | ★★★★☆ Multiple | ★★★★★ Extensive | ★★★★★ Custom (LiteLLM) |
| **Sharing** | ★★☆☆☆ Export | ★★★★★ Built-in | ★★★★☆ Good | ❌ Not for sharing |
| **Performance** | ★★★☆☆ Medium | ★★★★★ Fast | ★★★★☆ Fast | ★★★★★ Fast (CLI) |
| **Storage** | Local + NAS | Own database | Own database | NAS (source of truth) |
| **iPhone Verification** | ❌ No | ❌ No | ❌ No | ★★★★★ **YES** (critical!) |
| **Metadata** | XMP sidecars | Own DB | Own DB + XMP | XMP sidecars (universal) |
| **Deduplication** | ★★☆☆☆ Basic | ★★★★☆ Good | ★★★☆☆ Basic | ★★★★★ SHA256 + perceptual |
| **life-log Integration** | ❌ No | ❌ No | ❌ No | ★★★★★ **YES** (diary export) |

---

## Use Case Recommendations

### For Your Workflow

**When to use digiKam**:
- ✅ Local photo editing (RAW, exposure, color)
- ✅ Album organization
- ✅ Batch operations (renaming, tagging)
- ✅ Existing workflow on NixOS desktop
- ✅ Offline access

**When to use Immich**:
- ✅ Mobile photo upload from iPhone
- ✅ Sharing photos with family/friends
- ✅ Quick browsing on phone/tablet
- ✅ Facial recognition (automatic albums)
- ✅ Mobile backup

**When to use PhotoPrism**:
- ✅ Web browsing (from any device)
- ✅ AI-powered search ("beach", "sunset", "daughter smiling")
- ✅ Place/map view
- ✅ No desktop app needed

**When to use picture-pipeline**:
- ✅ **iPhone photo verification** (prove location/time) - **CRITICAL**
- ✅ Deduplication across all sources
- ✅ life-log diary reconstruction
- ✅ Dawarich location export
- ✅ Screenshot management
- ✅ Source of truth for all tools

---

## Recommended Architecture: "Best of All Worlds"

```
┌─────────────────────────────────────────────────────┐
│ picture-pipeline (Source of Truth)                  │
│                                                       │
│ • iPhone verification (CRITICAL)                    │
│ • Deduplication (SHA256 + perceptual)              │
│ • Metadata extraction (ExifTool)                    │
│ • Storage management (hot/warm/cold)                │
│ • XMP sidecars (universal metadata)                 │
│ • life-log export (diary events)                    │
│ • Dawarich export (location timeline)               │
│                                                       │
│ Storage: /mnt/nas/photos/originals/                 │
└─────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┴─────────────────┐
        ↓                 ↓                   ↓
┌───────────────┐ ┌───────────────┐ ┌──────────────────┐
│ Immich        │ │ digiKam       │ │ PhotoPrism       │
│ (Mobile)      │ │ (Desktop)     │ │ (Web)            │
├───────────────┤ ├───────────────┤ ├──────────────────┤
│ • Mobile app  │ │ • Photo edit  │ │ • Web UI         │
│ • Share       │ │ • Albums      │ │ • AI search      │
│ • Face recog  │ │ • Tags        │ │ • Map view       │
│               │ │               │ │                  │
│ Mode:         │ │ Mode:         │ │ Mode:            │
│ External lib  │ │ Direct NAS    │ │ Index NAS        │
│ (read-only)   │ │ (read-write)  │ │ (read XMP)       │
└───────────────┘ └───────────────┘ └──────────────────┘
        ↓                 ↓                   ↓
        └─────────────────┴─────────────────┘
                          ↓
              All read from same NAS:
              /mnt/nas/photos/originals/
              (Managed by picture-pipeline)
```

---

## Configuration for Each Tool

### 1. picture-pipeline (Master)

**Purpose**: Import, verify, deduplicate, manage storage

**Config**:
```yaml
# config/storage.yaml
storage:
  nas:
    base_path: "/mnt/nas/photos"
    originals: "originals/{year}/{month}/{day}"
    sidecars: "originals/{year}/{month}/{day}"

  sync_source: "docker-icloud"  # Or Immich mobile upload
```

**What it does**:
- Imports from iCloud (Docker container)
- Verifies iPhone photos (GPS, timestamp)
- Generates thumbnails (local)
- Writes XMP sidecars (for other tools)
- Exports to life-log (diary events)

---

### 2. Immich (Mobile + Sharing)

**Purpose**: Mobile app, automatic upload, sharing

**Config**:
```yaml
# Immich: External Library mode (read-only)
external_libraries:
  - name: "picture-pipeline"
    path: "/mnt/nas/photos/originals"
    import_path: "/mnt/nas/photos/originals"
    scan_interval: "1h"
    exclusion_pattern: ""
```

**Workflow**:
1. Take photo on iPhone
2. Auto-upload to Immich (mobile app)
3. Immich stores in `/mnt/nas/photos/immich-upload/`
4. picture-pipeline watches, processes, moves to `/mnt/nas/photos/originals/`
5. Immich sees photo in external library

**Benefits**:
- ✅ Best mobile experience
- ✅ Automatic backup from phone
- ✅ Easy sharing with family
- ✅ Fast face recognition

**Drawback**:
- ❌ No iPhone verification (picture-pipeline does this)

---

### 3. digiKam (Desktop Editing)

**Purpose**: Photo editing, album organization

**Config**:
```ini
# ~/.config/digikamrc
[Database Settings]
Database Type=SQLite
Database Name=/mnt/nas/photos/digikam.db

[Album Settings]
Album Path=/mnt/nas/photos/originals
Album Hierarchy=Year/Month/Day

[Metadata Settings]
Read Metadata From Sidecars=true
Write Metadata To Sidecars=true
Sidecar Format=XMP

[Thumbnail Settings]
Thumbnail Path=/home/user/.local/share/pictures/thumbs
```

**Workflow**:
1. Open digiKam on desktop
2. Points to `/mnt/nas/photos/originals/` (same as picture-pipeline)
3. Reads XMP sidecars (written by picture-pipeline)
4. Edit photos, create albums, add tags
5. Writes changes back to XMP (picture-pipeline re-imports)

**Benefits**:
- ✅ Best photo editor
- ✅ Full RAW support
- ✅ Batch operations
- ✅ Shares thumbnails with picture-pipeline (performance)

---

### 4. PhotoPrism (Web Browsing)

**Purpose**: Web UI, AI search, map view

**Config**:
```yaml
# docker-compose.yml for PhotoPrism
services:
  photoprism:
    image: photoprism/photoprism:latest
    environment:
      PHOTOPRISM_ORIGINALS_PATH: "/photoprism/originals"
      PHOTOPRISM_STORAGE_PATH: "/photoprism/storage"
      PHOTOPRISM_SIDECAR_PATH: "/photoprism/originals"
      PHOTOPRISM_SIDECAR_YAML: "true"
      PHOTOPRISM_SIDECAR_JSON: "false"
      PHOTOPRISM_SIDECAR_IMPORT: "true"
    volumes:
      - /mnt/nas/photos/originals:/photoprism/originals:ro  # Read-only!
      - /mnt/nas/photos/photoprism-storage:/photoprism/storage
```

**Workflow**:
1. PhotoPrism scans `/mnt/nas/photos/originals/`
2. Reads XMP sidecars (from picture-pipeline)
3. Indexes photos, builds own database
4. AI features (face recognition, object detection)
5. **Read-only mode** (doesn't modify originals)

**Benefits**:
- ✅ Best web UI
- ✅ AI-powered search
- ✅ Map view (uses GPS from iPhone photos)
- ✅ Works from any device

---

## Data Flow

### Import Flow

```
iPhone → iCloud → Docker iCloud Backup
                      ↓
              picture-pipeline
                      ↓
         1. iPhone verification (GPS, timestamp)
         2. Deduplication (SHA256 + perceptual)
         3. Metadata extraction (ExifTool)
         4. Face recognition (daughter, family)
         5. Aesthetic scoring (LLM)
         6. XMP sidecar generation
         7. Storage (organized by date)
                      ↓
         /mnt/nas/photos/originals/YYYY/MM/DD/
                      ↓
         ┌────────────┴────────────┐
         ↓            ↓             ↓
      Immich      digiKam     PhotoPrism
     (mobile)    (desktop)       (web)
```

### Editing Flow

```
digiKam (Edit photo)
    ↓
XMP sidecar updated
    ↓
picture-pipeline (Re-import XMP)
    ↓
PostgreSQL database updated
    ↓
Other tools see updated metadata
```

---

## Storage Usage

### With picture-pipeline as Master

| Component | Storage | Size (50k photos) |
|-----------|---------|-------------------|
| picture-pipeline originals | /mnt/nas/photos/originals | 500 GB (JPG/H.264) |
| picture-pipeline thumbnails | ~/.local/share/pictures/thumbs | 15 GB (local) |
| picture-pipeline sidecars | /mnt/nas/photos/originals | 500 MB (XMP) |
| Immich database | /mnt/nas/photos/immich-storage | 5 GB |
| Immich thumbnails | /mnt/nas/photos/immich-storage | 20 GB |
| digiKam database | /mnt/nas/photos/digikam.db | 2 GB |
| digiKam thumbnails | Shared with picture-pipeline | 0 GB (symlink) |
| PhotoPrism database | /mnt/nas/photos/photoprism-storage | 10 GB |
| PhotoPrism thumbnails | /mnt/nas/photos/photoprism-storage | 25 GB |
| **Total** | | **~580 GB** |

**Without picture-pipeline** (each tool independent):
- Originals × 3 (duplicated): 1,500 GB
- Thumbnails × 3 (not shared): 60 GB
- Total: ~1,600 GB (**3x more storage!**)

---

## Recommended Workflow

### Daily Use

1. **Take photos on iPhone** → Auto-upload to Immich (mobile app)
2. **Browse on phone** → Use Immich mobile app
3. **Browse on web** → Use PhotoPrism (AI search, map view)
4. **Edit on desktop** → Use digiKam (RAW editing, albums)
5. **Verify for life-log** → picture-pipeline runs automatically

### Weekly Review

1. **Run picture-pipeline** → Process new photos, verify iPhones
2. **Check duplicates** → picture-pipeline finds and reports
3. **Train faces** → Add new family photos to recognition
4. **Export to life-log** → Generate diary events from verified photos

### Special Tasks

- **Share with family**: Use Immich (best sharing)
- **Print photos**: Export from digiKam (best quality)
- **Find "beach photos"**: Use PhotoPrism (best AI search)
- **Prove location**: Use picture-pipeline (iPhone verification)

---

## Migration Path

### Phase 1: Set up picture-pipeline (Week 1)
- Import existing photos
- Verify iPhone photos
- Generate thumbnails
- Write XMP sidecars

### Phase 2: Add Immich (Week 2)
- Set up external library pointing to NAS
- Configure mobile app
- Test automatic upload

### Phase 3: Configure digiKam (Week 3)
- Point to NAS originals
- Import XMP sidecars
- Share thumbnails with picture-pipeline
- Test editing workflow

### Phase 4: Add PhotoPrism (Week 4)
- Set up read-only scanning
- Index photos
- Test AI search
- Test map view

---

## Summary: Why All Three?

**You want ALL THREE because**:

1. **Immich** = **Mobile** experience (upload, share, browse on phone)
2. **digiKam** = **Desktop** editing (RAW, batch ops, albums)
3. **PhotoPrism** = **Web** browsing (AI search, any device)
4. **picture-pipeline** = **Source of truth** (iPhone verification, deduplication, life-log)

**They DON'T conflict** - they complement each other:
- All read from same NAS storage
- All respect XMP sidecars
- picture-pipeline ensures no duplicates
- Each excels at what it does best

**Single tool would compromise**:
- Immich-only: No desktop editing, no iPhone verification
- digiKam-only: No mobile app, no web access
- PhotoPrism-only: No mobile app, no advanced editing, no iPhone verification
- picture-pipeline-only: Not a photo viewer/editor

**Best of all worlds = All four working together!** 🎯
