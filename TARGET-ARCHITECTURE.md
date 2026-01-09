# TARGET-ARCHITECTURE

**Current state vs target state per component**

---

## Component: iPhone Photo Verification

| Aspect | Current | Target |
|--------|---------|--------|
| ExifTool Integration | ✅ Working | ✅ Same |
| Metadata Extraction | ✅ ALL tags | ✅ Same |
| iPhone Detection | ✅ Make, model, iOS | ✅ Same |
| GPS Extraction | ✅ Coordinates parsed | ✅ Same |
| Confidence Scoring | ✅ 0.0-1.0 scale | ✅ Same |
| Apple-Specific Tags | ✅ HDR/Live Photo | ✅ Same |
| CLI Tool | ✅ verify-iphone command | ✅ Same |
| Testing | ✅ Unit tests | ✅ Same |

**Gap:** ✅ NONE - Fully implemented!

---

## Component: Import Pipeline

| Aspect | Current | Target |
|--------|---------|--------|
| icloudpd Import | ❌ Not implemented | ✅ Import 51,187 photos |
| iphoneSync Import | ❌ Not implemented | ✅ Import +10,136 unique |
| Metadata Merger | ❌ Not implemented | ✅ GPS from icloudpd + HDR from iphoneSync |
| Database Storage | ❌ Not implemented | ✅ PostgreSQL + pgvector |
| Progress Tracking | ❌ Not implemented | ✅ Resume on failure |

**Gap:** Full import pipeline (v0.2.0 milestone)

---

## Component: Deduplication

| Aspect | Current | Target |
|--------|---------|--------|
| SHA256 Hashing | ❌ Not implemented | ✅ File-level exact duplicates |
| pHash (Perceptual) | ❌ Not implemented | ✅ Visual similarity (cropped, resized) |
| Duplicate Detection | ❌ Not implemented | ✅ Find visually similar photos |
| Storage Strategy | ❌ Not implemented | ✅ One physical copy, multiple refs |
| User Review UI | ❌ Not implemented | ✅ Confirm before deletion |

**Gap:** Full deduplication system (v0.2.0 milestone)

---

## Component: Thumbnail Generation

| Aspect | Current | Target |
|--------|---------|--------|
| 150px Thumbnails | ❌ Not implemented | ✅ Grid view (HOT tier: SSD) |
| 500px Previews | ❌ Not implemented | ✅ Quick preview (WARM tier: HDD) |
| 1920px Display | ❌ Not implemented | ✅ Full-screen view (WARM tier: HDD) |
| Format | ❌ Not implemented | ✅ WebP for size savings |
| Generation | ❌ Not implemented | ✅ Async queue processing |

**Gap:** Three-tier thumbnail system (v0.2.0 milestone)

---

## Component: XMP Sidecar Management

| Aspect | Current | Target |
|--------|---------|--------|
| XMP Writing | ❌ Not implemented | ✅ Standard XMP format |
| Person Tags | ❌ Not implemented | ✅ mwg-rs:Regions standard |
| GPS Coordinates | ❌ Not implemented | ✅ exif:GPS* tags |
| Aesthetic Score | ❌ Not implemented | ✅ custom:AestheticScore |
| iPhone Verification | ❌ Not implemented | ✅ custom:iPhoneVerified |
| Git Versioning | ❌ Not implemented | ✅ Track XMP changes |

**Gap:** Complete XMP sidecar system (v0.2.0-v0.4.0)

---

## Component: Person Tagging

| Aspect | Current | Target |
|--------|---------|--------|
| Face Detection | ❌ Not implemented | ✅ LiteLLM vision models |
| Person Recognition | ❌ Not implemented | ✅ Daughter, spouse, family |
| XMP Integration | ❌ Not implemented | ✅ mwg-rs:Regions write |
| digiKam Sync | ❌ Not implemented | ✅ Bi-directional sync |
| PhotoPrism/Immich | ❌ Not implemented | ✅ Read XMP tags |
| Age Tracking | ❌ Not implemented | ✅ Daughter: months, adults: years |

**Gap:** Full person tagging system (v0.3.0 milestone)

---

## Component: AI Enrichment

| Aspect | Current | Target |
|--------|---------|--------|
| Aesthetic Scoring | ❌ Not implemented | ✅ 0-10 quality rating |
| Auto-Captioning | ❌ Not implemented | ✅ Descriptive sentences |
| Hierarchical Tags | ❌ Not implemented | ✅ IPTC: scene, subject, activity, mood |
| Reverse Geocoding | ❌ Not implemented | ✅ GPS → "Cologne, Germany" |
| Screenshot OCR | ❌ Not implemented | ✅ Text extraction via vision LLM |
| Content Classification | ❌ Not implemented | ✅ Camera vs downloaded vs screenshot |

**Gap:** Full AI enrichment (v0.4.0 milestone)

---

## Component: Storage Tiers

| Aspect | Current | Target |
|--------|---------|--------|
| Structure | ❌ Not implemented | ✅ YYYY/YYYY-MM/pictures/videos |
| HOT Tier | ❌ Not implemented | ✅ Thumbnails (SSD) |
| WARM Tier | ❌ Not implemented | ✅ Full-res 2019+ (NAS HDD) |
| COLD Tier | ❌ Not implemented | ✅ Full-res <2019 (USB backup) |
| Immutability | ❌ Not implemented | ✅ chmod 444 originals |
| On-Demand Load | ❌ Not implemented | ✅ COLD → WARM when accessed |

**Gap:** Three-tier storage system (v0.2.0-v0.3.0)

---

## Component: Database Schema

| Aspect | Current | Target |
|--------|---------|--------|
| PostgreSQL | ❌ Not created | ✅ Core storage |
| pgvector Extension | ❌ Not created | ✅ Face embeddings |
| Apache AGE | ❌ Not created | ✅ Photo relationships |
| Tables | ❌ Not created | ✅ images, faces, people, tool_refs |
| Indexes | ❌ Not created | ✅ Optimized queries |

**Gap:** Full database schema (v0.2.0 milestone)

---

## Component: Tool Integration

| Aspect | Current | Target |
|--------|---------|--------|
| digiKam | ❌ Not integrated | ✅ Read/write XMP |
| PhotoPrism | ❌ Not integrated | ✅ Import XMP tags |
| Immich | ❌ Not integrated | ✅ API integration |
| Damselfly | ❌ Not integrated | ✅ Symlink support |
| Picture Frame | ❌ Not integrated | ✅ REST API + Pi client |

**Gap:** Multi-tool integration (v0.6.0 milestone)

---

## Component: life-log Integration

| Aspect | Current | Target |
|--------|---------|--------|
| Event Reconstruction | ❌ Not implemented | ✅ Photos → diary entries |
| Location Timeline | ❌ Not implemented | ✅ GPS → Dawarich export |
| Person Timeline | ❌ Not implemented | ✅ "Daughter's activities" |
| Project Linking | ❌ Not implemented | ✅ Screenshots → RAG projects |
| Obsidian Export | ❌ Not implemented | ✅ Daily note integration |

**Gap:** Full life-log system (v0.5.0-v0.6.0)

---

## Component: Screenshot Pipeline

| Aspect | Current | Target |
|--------|---------|--------|
| Auto-Sync | ❌ Not implemented | ✅ Watch folder → import |
| OCR | ❌ Not implemented | ✅ Text extraction |
| Intelligent Renaming | ❌ Not implemented | ✅ LLM-based naming |
| Keyword Extraction | ❌ Not implemented | ✅ Link to projects |
| Text Search | ❌ Not implemented | ✅ Full-text search |

**Gap:** Screenshot pipeline (v0.4.0-v0.5.0)

---

## Technology Stack

| Layer | Current | Target |
|-------|---------|--------|
| Language | Python 3.11+ | Same |
| Database | ❌ None | PostgreSQL + pgvector + Apache AGE |
| LLM Client | ❌ None | LiteLLM (vision models) |
| Metadata | ExifTool (working) | Same + XMP toolkit |
| Image Processing | ❌ None | Pillow/PIL |
| Hashing | ❌ None | hashlib (SHA256) + ImageHash (pHash) |
| Face Detection | ❌ None | LiteLLM vision models |
| Storage | ❌ None | Tiered (SSD/HDD/USB) |
| Container | Dockerfile (working) | Same |

**Gap:** Add database, LLM client, image processing libraries

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Import Sources                                                  │
│ ├─ icloudpd (51,187 photos) → GPS metadata rich               │
│ ├─ iphoneSync (+10,136 unique) → HDR metadata rich            │
│ └─ Manual imports                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Import Pipeline (v0.2.0)                                        │
│ ├─ SHA256 + pHash deduplication                                │
│ ├─ iPhone verification (✅ WORKING)                            │
│ ├─ Metadata merger                                              │
│ └─ Database insertion                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Storage Tiers                                                   │
│ ├─ HOT (SSD): Thumbnails (150px/500px/1920px)                 │
│ ├─ WARM (HDD): Full-res 2019+ (NAS)                           │
│ └─ COLD (USB): Full-res <2019 (on-demand)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Enrichment Pipeline (v0.3.0-v0.4.0)                            │
│ ├─ Person tagging (LiteLLM vision)                             │
│ ├─ Aesthetic scoring (0-10)                                     │
│ ├─ Auto-captioning                                              │
│ ├─ Screenshot OCR                                               │
│ └─ XMP sidecar generation                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Tool Integrations (v0.6.0)                                      │
│ ├─ digiKam (XMP bi-directional sync)                           │
│ ├─ PhotoPrism (XMP import)                                      │
│ ├─ Immich (API integration)                                     │
│ ├─ Damselfly (symlinks)                                         │
│ └─ Picture Frame (REST API + Pi client)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ life-log Integration (v0.5.0-v0.6.0)                           │
│ ├─ Event reconstruction ("Daughter's day")                     │
│ ├─ Location timeline (Dawarich export)                         │
│ ├─ Project linking (screenshots → RAG)                         │
│ └─ Obsidian daily notes                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Current vs Target Summary

| Milestone | Status | Completion | Notes |
|-----------|--------|------------|-------|
| v0.1.0 Foundation | ✅ DONE | 100% | iPhone verification working! |
| v0.2.0 Import | 🚧 Not started | 0% | Database + import pipeline |
| v0.3.0 Person Tagging | 🚧 Not started | 0% | Face detection + XMP sync |
| v0.4.0 AI Enrichment | 🚧 Not started | 0% | Scoring + captioning |
| v0.5.0 Project Linking | 🚧 Not started | 0% | Screenshot pipeline |
| v0.6.0 Integrations | 🚧 Not started | 0% | Tool integration |
| v1.0.0 Stable | 🚧 Not started | 0% | Production ready |

**Overall completion:** 14% (v0.1.0 done, 6 milestones remaining)

---

*This file should be updated as milestones are completed.*
