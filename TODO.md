# TODO.md

Tasks for v1.0.0 MVP

---

## Current Sprint: Testing & Import

### HIGH PRIORITY

- [ ] **Test iPhone verification with real photos**
  - Find 5-10 iPhone photos with GPS
  - Run `./run.sh verify-iphone` on each
  - Verify GPS coordinates are correct
  - Verify confidence scores make sense
  - Test with non-iPhone photos (should reject)

- [ ] **Implement SHA256 hashing**
  - Create `src/deduplication/hashing.py`
  - Calculate SHA256 for files
  - Store in database

- [ ] **Create database schema**
  - Create `photos` schema in PostgreSQL
  - Create `photos.images` table
  - Create indexes (sha256, date_taken, is_iphone_photo)
  - Test connection from picture-pipeline

- [ ] **Build basic import script**
  - Create `src/ingestion/import_photos.py`
  - Import single photo
  - Extract metadata (via iPhone verifier)
  - Store in database
  - Move to organized structure (YYYY/MM/DD)

---

## MEDIUM PRIORITY

- [ ] **Thumbnail generation**
  - Create `src/storage/thumbnails.py`
  - Generate 3 sizes (tiny, small, medium)
  - Store in ~/.local/share/pictures/thumbs/
  - Test with HEIC, JPG, PNG

- [ ] **Perceptual hashing**
  - Integrate imagehash library
  - Calculate pHash, dHash
  - Store in database
  - Find similar images (0.95+ similarity)

- [ ] **Storage tier management**
  - Create `src/storage/tier_manager.py`
  - Move photos between hot/warm/cold
  - Track access patterns
  - Auto-migration rules (age, score, faces)

---

## LOW PRIORITY (Post-MVP)

- [ ] **Face recognition training**
  - Create `src/faces/training.py`
  - Collect 20-30 photos of daughter
  - Generate face encodings
  - Store in `photos.people` table

- [ ] **Face matching**
  - Create `src/faces/recognition.py`
  - Detect faces in photos
  - Match against trained encodings
  - 95%+ confidence threshold

- [ ] **XMP sidecar generation**
  - Create `src/metadata/xmp_writer.py`
  - Write iPhone verification to XMP
  - Write face identifications to XMP
  - Write aesthetic scores to XMP

- [ ] **life-log event export**
  - Create `src/integration/lifelog.py`
  - Export verified iPhone photos as events
  - Include location, people, activity type
  - Store in lifelog.events table

- [ ] **Dawarich location export**
  - Create `src/integration/dawarich.py`
  - Export GPS waypoints from verified photos
  - Format for Dawarich import
  - Include metadata (people, activity)

---

## Backlog

- [ ] Batch import (directory scan)
- [ ] Progress reporting (tqdm)
- [ ] Error handling and logging
- [ ] Screenshot detection and renaming
- [ ] Video format conversion (HEVC → H.264)
- [ ] HEIC format conversion (HEIC → JPG)
- [ ] Immich integration (external library)
- [ ] digiKam integration (shared thumbnails)
- [ ] PhotoPrism integration (scan XMP)
- [ ] Aesthetic scoring (vision LLM)
- [ ] Scene description (vision LLM)
- [ ] Weekly/monthly reports
- [ ] Obsidian vault generation
- [ ] Duplicate photo finder UI
- [ ] Storage usage dashboard

---

## Completed ✅

- [x] iPhone photo verification
- [x] ExifTool integration
- [x] GPS coordinate parsing
- [x] Confidence scoring
- [x] Project structure
- [x] Configuration management
- [x] Unit tests (iPhone verifier)
- [x] CLI tool (verify-iphone)
- [x] Documentation (7,800+ lines)

---

*Updated by TodoWrite tool*
*Focus: Get iPhone verification tested with real photos!*
