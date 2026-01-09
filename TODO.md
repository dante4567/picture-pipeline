# TODO.md

Tasks for v0.2.0 - Import Pipeline

---

## Current Sprint: Import Pipeline

### HIGH PRIORITY

- [ ] **Create database schema**
  - Create `photos` schema in PostgreSQL
  - Create `photos.images` table
  - Create `photos.people` table
  - Create `photos.faces` table
  - Create indexes (sha256, phash, date_taken, is_iphone_photo)
  - Test connection from picture-pipeline

- [ ] **Build import pipeline**
  - Create `src/ingestion/import_photos.py`
  - Import from icloudpd source (51,187 photos)
  - Extract metadata (GPS, camera, date)
  - Calculate SHA256 + pHash
  - Store in database with provenance
  - Generate XMP sidecars

- [ ] **Implement metadata merger**
  - Create `src/metadata/merger.py`
  - Detect duplicate photos by pHash
  - Merge GPS from icloudpd + HDR from iphoneSync
  - Write merged metadata to XMP
  - Track sources in database

- [ ] **Thumbnail generation**
  - Create `src/storage/thumbnails.py`
  - Generate 3 sizes (150px, 500px, 1920px)
  - Store in ~/.local/share/pictures/thumbs/
  - Test with HEIC, JPG, PNG

---

## MEDIUM PRIORITY

- [ ] **Git versioning for sidecars**
  - Create `src/metadata/git_sidecar.py`
  - Auto-commit XMP changes
  - Structured commit messages
  - CLI: `./run.sh history <photo_hash>`

- [ ] **Storage organization**
  - Move photos to YYYY/YYYY-MM/pictures|videos structure
  - Set originals to read-only (chmod 444)
  - Create .gitignore for originals (only track XMP)
  - Initialize Git repo in originals/

- [ ] **Import from iphoneSync**
  - Skip duplicates (check pHash)
  - Merge metadata with icloudpd photos
  - Import unique photos only (+10,136)

---

## LOW PRIORITY (v0.3.0 - Person Tagging)

- [ ] **Person face detection**
  - Use LiteLLM vision model for face detection
  - Create `src/faces/detection.py`
  - Store face regions in database

- [ ] **XMP person tagging**
  - Write mwg-rs:Regions to XMP
  - Read person tags from digiKam
  - Sync to database

- [ ] **Age tracking**
  - Calculate age from birthdate
  - Store in months (daughter) or years (adults)
  - Query photos by age range

---

## Backlog (v0.4.0+)

- [ ] AI enrichment (aesthetic scoring, captioning, tags)
- [ ] Sequence detection (photos within 5 minutes)
- [ ] Project linking (keywords → RAG repos)
- [ ] Obsidian daily note integration
- [ ] Picture frame server API
- [ ] Raspberry Pi display client
- [ ] Downloaded photo classification (Twitter, Instagram, etc.)
- [ ] Screenshot text extraction (OCR via vision LLM)

---

## Completed ✅

### v0.1.0 - Foundation (2026-01-09)
- [x] iPhone photo verification
- [x] ExifTool integration
- [x] SHA256 + pHash hashing implementation
- [x] Docker build system
- [x] NAS photo source analysis (200 sample photos)
- [x] Project structure and conventions
- [x] Comprehensive documentation (9 docs, 5,000+ lines)
- [x] Obsidian integration documentation
- [x] Picture frame integration documentation
- [x] Migrated to repo-template structure
- [x] GitHub repo created and pushed

---

*Updated: 2026-01-09*
*Next: Database schema → Import pipeline → Metadata merger*
