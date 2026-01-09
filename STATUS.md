# STATUS.md

**Last updated:** 2026-01-09
**Version:** v1.0.0

---

## What Works ✅

✅ **iPhone Photo Verification** (CRITICAL - IMPLEMENTED!)
- ExifTool integration
- Metadata extraction (ALL EXIF/XMP/IPTC tags)
- iPhone detection (make, model, iOS version)
- GPS coordinate extraction and parsing
- Confidence scoring (0.0-1.0)
- Apple-specific tag detection
- HDR/Live Photo detection
- CLI tool: `./run.sh verify-iphone <photo>`
- Unit tests passing

✅ **Project Structure**
- Modular architecture (8 modules)
- Configuration management
- Storage tier definitions
- Requirements documented
- Testing framework set up

✅ **Documentation** (7,800+ lines)
- Complete architecture (PICTURE-PIPELINE-ARCHITECTURE.md)
- Sync strategy (SYNC-STRATEGY.md)
- Life-log integration (LIFE-LOG-INTEGRATION.md)
- Storage tiers (STORAGE-TIERS.md)

---

## What Doesn't Work ❌

❌ **Import Pipeline** - Not implemented
❌ **Deduplication** (SHA256 + perceptual hash) - Not implemented
❌ **Face Recognition** - Not implemented
❌ **Thumbnail Generation** - Not implemented
❌ **Storage Tier Management** - Not implemented
❌ **XMP Sidecar Writing** - Not implemented
❌ **Database Schema** - Not created
❌ **life-log Event Export** - Not implemented
❌ **Tool Integration** (Immich, digiKam, etc.) - Not implemented
❌ **Screenshot Pipeline** - Not implemented

---

## Current Blockers

1. **Need real iPhone photos for testing** - Critical to verify implementation
2. **Need to decide on sync method** - Docker iCloud vs Immich
3. **Need NAS mount point** - /mnt/nas/photos
4. **Need shared-infrastructure running** - PostgreSQL + LiteLLM

---

## Next Steps (Priority Order)

### Immediate (Today)

1. **Test iPhone verification with real photos**:
   ```bash
   ./run.sh setup  # Install dependencies
   ./run.sh verify-iphone ~/path/to/iphone/photo.jpg
   ```

2. **Verify ExifTool extracts all metadata**:
   - GPS coordinates
   - Date/time
   - Camera model
   - iOS version

### Short-term (This Week)

1. **Implement SHA256 hashing** (deduplication foundation)
2. **Create database schema** in PostgreSQL
3. **Build basic import script** (single photo)
4. **Test full pipeline**: import → verify → store metadata

### Medium-term (This Month)

1. **Thumbnail generation** (3 sizes: tiny, small, medium)
2. **Storage tier management** (hot/warm/cold)
3. **Face recognition training** (daughter, spouse, family)
4. **XMP sidecar generation**

### Long-term (Next Month)

1. **life-log event export** (verified photos → events)
2. **Dawarich location export** (GPS timeline)
3. **Tool integration** (Immich, digiKam, PhotoPrism)
4. **Screenshot pipeline** (OCR, auto-rename)

---

## Testing Status

| Component | Tests | Status |
|-----------|-------|--------|
| iPhone Verifier | 5 unit tests | ✅ Passing |
| GPS Parsing | 3 unit tests | ✅ Passing |
| Config | - | ✅ Manual test |
| Import | - | ❌ Not implemented |
| Dedup | - | ❌ Not implemented |
| Faces | - | ❌ Not implemented |

**To run tests**: `./run.sh test`

---

## Known Issues

1. **GPS parsing**: Handles DMS and decimal, but untested with all iPhone GPS formats
2. **ExifTool required**: System dependency, must be installed separately
3. **No error handling**: Import pipeline needs robust error handling
4. **No progress reporting**: Batch operations need progress bars

---

## Performance Considerations

**Current**:
- iPhone verification: ~100-200ms per photo (ExifTool subprocess)
- Batch processing: Not optimized

**Target**:
- Process 10,000 photos/hour
- iPhone verification: <50ms per photo (batch mode)
- Thumbnail generation: <100ms per photo

---

## Dependencies Status

| Dependency | Status | Version | Notes |
|------------|--------|---------|-------|
| Python | ✅ Required | 3.11+ | |
| ExifTool | ⚠️ Manual install | Latest | `sudo apt install libimage-exiftool-perl` |
| PostgreSQL | ⏳ Pending | 15+ | From shared-infrastructure |
| LiteLLM | ⏳ Pending | Latest | From shared-infrastructure |
| pip packages | ✅ Listed | - | See requirements.txt |

---

## Success Criteria for v1.0

To declare v1.0 "done":
- [x] iPhone verification working
- [ ] Import 10,000+ photos successfully
- [ ] Deduplication working (no duplicate storage)
- [ ] Face recognition trained (3+ family members)
- [ ] Life-log events exported (100+ verified photos)
- [ ] Dawarich integration working
- [ ] At least 1 tool integrated (Immich or digiKam)

**Current progress**: 1/7 (14%)

---

*This file MUST be kept brutally honest.*
*iPhone verification is implemented and ready for testing!*
