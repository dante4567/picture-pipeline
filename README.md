# picture-pipeline

Centralized photo management system - source of truth for all photo tools.

## Purpose

Transform scattered photo collections into an organized, searchable, verifiable archive:
1. **Deduplication** - SHA256 + perceptual hashing
2. **iPhone Verification** - Prove "I was at X location at Y time" (legal proof)
3. **Face Recognition** - Zero false positives for family (especially daughter)
4. **Smart Storage** - Thumbnails local (fast), full-res on NAS (on-demand)
5. **Tool Integration** - Works with Immich, PhotoPrism, digiKam, Damselfly
6. **Life-log Integration** - Reverse-engineered diary from photos
7. **Screenshot Management** - Auto-sync, OCR, intelligent renaming

## Status

v1.0.0 - Architecture complete, implementation pending

| Feature | Status | Notes |
|---------|--------|-------|
| Architecture docs | ✅ Complete | See docs/ folder |
| iPhone verification | 🚧 Planned | ExifTool + Apple metadata |
| Face recognition | 🚧 Planned | DeepFace, 95%+ confidence |
| Storage tiers | 🚧 Planned | Hot/warm/cold |
| Screenshot pipeline | 🚧 Planned | OCR + auto-rename |
| Life-log export | 🚧 Planned | Event generation |
| Tool integration | 🚧 Planned | Immich, digiKam, PhotoPrism |

## Quick Start

```bash
# Set up storage configuration
./run.sh setup-storage

# Import existing photos
./run.sh import /path/to/photos

# Generate thumbnails
./run.sh generate-thumbs

# Train face recognition (family photos)
./run.sh train-faces /path/to/training

# Start continuous sync
./run.sh sync --daemon
```

## Architecture

See comprehensive documentation:
- [PICTURE-PIPELINE-ARCHITECTURE.md](docs/PICTURE-PIPELINE-ARCHITECTURE.md) - Complete system design
- [SYNC-STRATEGY.md](docs/SYNC-STRATEGY.md) - Consolidate sync methods
- [LIFE-LOG-INTEGRATION.md](docs/LIFE-LOG-INTEGRATION.md) - Reverse-engineered diary
- [STORAGE-TIERS.md](docs/STORAGE-TIERS.md) - Cold storage + screenshots

## Tech Stack

- Python 3.11+
- ExifTool (metadata extraction)
- face_recognition / DeepFace (face recognition)
- LiteLLM (aesthetic scoring, scene description)
- PostgreSQL + pgvector (metadata + face encodings)
- XMP sidecars (tool-agnostic metadata)

## Documentation

- [CLAUDE.md](CLAUDE.md) - Instructions for Claude Code
- [STATUS.md](STATUS.md) - Current state
- [TODO.md](TODO.md) - Implementation tasks
