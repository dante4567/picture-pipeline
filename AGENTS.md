# AGENTS.md
# Rules for ALL AI Agents (Claude, Codex, Gemini, etc.)

## 1. Conventions

- Entry point: `./run.sh`
- Language: Python 3.11+
- Package manager: pip (Docker-first, requirements.txt)
- Config: `.env` files (not committed)
- Infrastructure: shared-infrastructure (PostgreSQL, LiteLLM, Redis)

## 2. Autonomy Levels

| Level | You can do | Examples |
|-------|-----------|----------|
| L1 – Free | Do without asking | Bug fixes, refactoring, tests, docs |
| L2 – Summarize first | State intent, then proceed | New features, config changes |
| L3 – Stop and wait | Propose only, wait for approval | Architecture, new dependencies |

**Current level:** L2 (Summarize first)

## 3. Documentation Hygiene

After ANY change:
- Update README status table if behavior changed
- Update TODO.md to reflect completed/new tasks
- Run `./run.sh test` - must pass
- Commit with conventional message: `feat:`, `fix:`, `docs:`
- Update PLAN.md if milestone progress changed

## 4. Cross-Repo Awareness

| Related Repo | Relationship |
|--------------|--------------|
| shared-infrastructure | Upstream (provides PostgreSQL, LiteLLM, Redis) |
| life-log | Downstream (consumes photo metadata for diary) |
| rag-documents | Sibling (document processing patterns) |
| rag-ingestion | Sibling (metadata extraction patterns) |
| homelab | Infrastructure (NAS mounts, services) |

## 5. Current Focus

**Milestone:** v0.1 - Foundation
- SHA256 + pHash hashing ✅
- iPhone verification ✅
- Import pipeline (in progress)
- Person tagging with XMP sync
- Metadata merger (icloudpd + iphoneSync)

**Ignore for now:**
- AI enrichment (caption, tags) - comes after import pipeline
- Picture frame server - future feature
- Obsidian integration - future feature
- Scanned slides - future category

## 6. Never Without Approval

- Delete original photos (NEVER modify originals!)
- Change SHA256 hashing algorithm (breaks provenance)
- Modify XMP sidecar format (breaks tool compatibility)
- Add face recognition dependencies (use LiteLLM vision instead)
- Change storage structure (YYYY/YYYY-MM/pictures|videos)

## 7. Critical Principles

1. **Originals are sacred** - chmod 444, never modified
2. **XMP sidecars are universal** - All tools must use them
3. **SHA256 is identity** - Not just deduplication, provenance tracking
4. **pHash detects visual duplicates** - Different metadata, same content
5. **LiteLLM for all AI** - No direct OpenAI/Anthropic/Groq calls
6. **Docker-first** - All Python runs in containers

---

*Last updated: 2026-01-09*
