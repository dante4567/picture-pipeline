# PLAN

**Current version:** v0.1.0
**Target:** v1.0 = Consolidate all NAS photos with provenance tracking and universal person tagging

## Milestones

### ✅ v0.1.0 – Foundation (2026-01-09)
- [x] Project structure and documentation
- [x] SHA256 + pHash hashing implementation
- [x] iPhone photo verification (GPS temporal metadata)
- [x] NAS photo source analysis (icloudpd, iphoneSync, myPicturesFromMyIphone)
- [x] Docker build system
- [x] Comprehensive documentation suite (9 docs, ~5,000 lines)

**Key decisions:**
- Use both SHA256 (file identity) and pHash (visual similarity)
- XMP sidecars for universal metadata
- YYYY/YYYY-MM/pictures|videos storage structure
- Never modify originals (chmod 444)

###🔲 v0.2.0 – Import Pipeline (Target: 2026-01-20)
- [ ] Database schema (PostgreSQL + pgvector)
- [ ] Import photos from icloudpd (51,187 photos)
- [ ] Import photos from iphoneSync (+10,136 unique)
- [ ] Metadata merger (GPS from icloudpd + HDR from iphoneSync)
- [ ] Thumbnail generation (3 sizes: 150px, 500px, 1920px)
- [ ] XMP sidecar generation
- [ ] Git versioning for sidecars

### 🔲 v0.3.0 – Person Tagging (Target: 2026-02-01)
- [ ] Person face detection (via LiteLLM vision)
- [ ] XMP person tag read/write (mwg-rs:Regions standard)
- [ ] Bi-directional sync: digiKam ↔ XMP ↔ Database ↔ PhotoPrism/Immich
- [ ] Age tracking (daughter: months, adults: years)
- [ ] CLI: Tag person, list people, find photos by person

### 🔲 v0.4.0 – AI Enrichment (Target: 2026-02-15)
- [ ] Aesthetic scoring (0-10 quality rating via vision LLM)
- [ ] Auto-captioning (descriptive sentences)
- [ ] Hierarchical IPTC tags (scene, subject, activity, mood)
- [ ] Reverse geocoding (GPS → "Cologne, Germany")
- [ ] Text extraction from screenshots (OCR via vision LLM)
- [ ] Content classification (camera-taken vs downloaded vs screenshot)

### 🔲 v0.5.0 – Project Linking (Target: 2026-03-01)
- [ ] Sequence detection (photos taken within 5 minutes)
- [ ] Keyword extraction from screenshots
- [ ] Link to RAG projects (rag-ingestion, homelab, etc.)
- [ ] Project-based photo search
- [ ] Screenshot text search

### 🔲 v0.6.0 – Integrations (Target: 2026-03-15)
- [ ] Obsidian daily note integration ("On This Day" photos)
- [ ] life-log integration (diary reconstruction)
- [ ] Picture frame server API
- [ ] Raspberry Pi display client

### 🔲 v1.0.0 – Stable Release (Target: 2026-04-01)
- [ ] All core features working
- [ ] 136,053 photos consolidated → ~65,000 unique
- [ ] Test suite (pytest)
- [ ] Continuous imports (cron/systemd)
- [ ] Documentation complete
- [ ] Performance: <1 second search for "best photo of person X"

## Out of Scope (for now)

- Scanned slides integration (future category)
- Video processing (future, focus on photos first)
- Facial recognition training (use pre-trained models via LiteLLM)
- Cloud sync (focus on NAS-local first)
- Mobile app (future, use Immich for now)
- Printed photo digitization (future)

## Success Criteria (v1.0)

1. **Provenance:** Every photo has SHA256 hash (file identity)
2. **Deduplication:** pHash detects visual duplicates
3. **Person tagging:** Universal across all apps (digiKam, PhotoPrism, Immich)
4. **Search speed:** Find "best photo of daughter" in <1 second
5. **Safe deletion:** Can delete from iPhone after import (verified)
6. **Tool compatibility:** digiKam, PhotoPrism, Immich all work with same storage
7. **Metadata preservation:** GPS Date/Time stamps preserved from icloudpd

## Version History

| Version | Date | Key Features |
|---------|------|--------------|
| v0.1.0 | 2026-01-09 | Foundation, hashing, iPhone verification |

---

*Last updated: 2026-01-09*
