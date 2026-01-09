# Sync Strategy & Storage Optimization

Consolidate multiple sync methods and implement smart local storage.

---

## Current Sync Setup (To Consolidate)

You currently have **4 different sync methods**:

1. **iCloud sync on NAS** - Synology
2. **iOS Photos Sync app** - Dedicated app
3. **Proxmox container with Docker iCloud backup**
4. **Immich** - Photo management + sync

**Problem**: Redundancy, confusion, wasted storage

**Solution**: Choose **ONE** authoritative sync method, others become read-only consumers

---

## Recommended Architecture

### Central Authority: picture-pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ SOURCES (Read-Only)                                         │
├─────────────────────────────────────────────────────────────┤
│ • iPhone (via iCloud or USB import)                        │
│ • Camera imports (SD card, USB)                            │
│ • Existing photo libraries                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PICTURE-PIPELINE (Source of Truth)                         │
├─────────────────────────────────────────────────────────────┤
│ Storage:                                                     │
│ • NAS: /mnt/nas/photos/originals/<hash>.jpg (full-res)    │
│ • Local: ~/.local/share/pictures/thumbs/<hash>_*.jpg       │
│                                                              │
│ Database: PostgreSQL (metadata, hashes, locations)         │
│ Sidecars: XMP (person tags, scores, etc.)                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ CONSUMERS (Read-Only, Use Symlinks/Proxies)                │
├─────────────────────────────────────────────────────────────┤
│ • Immich: Reads from NAS, uses picture-pipeline DB         │
│ • PhotoPrism: Scans NAS, reads XMP sidecars                │
│ • digiKam: Points to NAS, reads sidecars                   │
│ • Damselfly: Symlinks to NAS originals                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Storage Strategy: Thumbnails Local, Full-Res On-Demand

### Goal
- **100% of pictures as thumbnails locally** (fast browsing)
- **Full resolution on NAS** (retrieved only when needed)
- **Works with any app** (Immich, digiKam, PhotoPrism)

### Implementation

#### 1. Thumbnail Sizes

Generate multiple thumbnail sizes:
- **Tiny**: 150x150 (grid view, fast loading)
- **Small**: 500x500 (browsing, quick preview)
- **Medium**: 1920x1080 (viewing, most use cases)
- **Full**: Original resolution on NAS (editing only)

#### 2. Local Storage (SSD)

```
~/.local/share/pictures/
├── thumbs/
│   ├── tiny/
│   │   └── <sha256_first_2>/<sha256>.jpg      # 150x150
│   ├── small/
│   │   └── <sha256_first_2>/<sha256>.jpg      # 500x500
│   ├── medium/
│   │   └── <sha256_first_2>/<sha256>.jpg      # 1920x1080
│   └── metadata/
│       └── <sha256_first_2>/<sha256>.json     # Quick metadata
├── cache/
│   └── full/                                   # Recently accessed full-res
│       └── <sha256_first_2>/<sha256>.jpg
└── config/
    └── storage.yaml
```

#### 3. NAS Storage (Full Resolution)

```
/mnt/nas/photos/
├── originals/
│   └── YYYY/
│       └── MM/
│           └── DD/
│               ├── <sha256>.jpg               # Original
│               └── <sha256>.xmp               # Sidecar
└── backups/
    └── icloud-archive/                         # Historical iCloud sync
```

#### 4. On-Demand Fetching

```python
class PhotoStorage:
    """Smart photo storage with on-demand fetching."""

    def get_photo(self, sha256: str, size: str = 'medium') -> bytes:
        """Get photo at specified size.

        Args:
            sha256: Photo hash
            size: 'tiny', 'small', 'medium', 'full'
        """
        # Check local cache first
        if size in ['tiny', 'small', 'medium']:
            thumb_path = self._get_thumb_path(sha256, size)
            if thumb_path.exists():
                return thumb_path.read_bytes()

        # For 'full', check local cache
        if size == 'full':
            cache_path = self._get_cache_path(sha256)
            if cache_path.exists():
                return cache_path.read_bytes()

            # Fetch from NAS
            nas_path = self._get_nas_path(sha256)
            if nas_path.exists():
                # Copy to cache for future access
                shutil.copy(nas_path, cache_path)
                return cache_path.read_bytes()

        raise FileNotFoundError(f"Photo {sha256} not found")

    def _get_thumb_path(self, sha256: str, size: str) -> Path:
        """Get thumbnail path."""
        prefix = sha256[:2]
        return Path(f"~/.local/share/pictures/thumbs/{size}/{prefix}/{sha256}.jpg").expanduser()

    def _get_cache_path(self, sha256: str) -> Path:
        """Get cache path for full-res."""
        prefix = sha256[:2]
        return Path(f"~/.local/share/pictures/cache/full/{prefix}/{sha256}.jpg").expanduser()

    def _get_nas_path(self, sha256: str) -> Path:
        """Get NAS path."""
        # Look up in database for YYYY/MM/DD
        photo = db.query(Photo).filter_by(sha256=sha256).first()
        return Path(f"/mnt/nas/photos/originals/{photo.date_path}/{sha256}.jpg")
```

---

## Sync Tool Decision Matrix

### Option 1: Docker iCloud Backup (RECOMMENDED)

**Tool**: Proxmox container with Docker iCloud backup

**Pros**:
- ✅ Runs 24/7 (no need for laptop to be on)
- ✅ Automatic sync from iCloud
- ✅ Server-based (Proxmox)
- ✅ Can be monitored/logged

**Cons**:
- ❌ Requires iCloud credentials
- ❌ Subject to Apple rate limits

**Integration**:
```yaml
# docker-compose.yml
services:
  icloud-sync:
    image: boredazfcuk/icloudpd:latest
    environment:
      - apple_id=your@email.com
      - notification_days=7
      - download_path=/photos
    volumes:
      - /mnt/nas/photos/icloud-sync:/photos
      - /mnt/nas/photos/config:/config
    restart: unless-stopped

  picture-pipeline:
    build: .
    depends_on:
      - icloud-sync
    volumes:
      - /mnt/nas/photos:/data
    command: watch /data/icloud-sync
```

**Flow**:
1. iCloud container syncs photos to `/mnt/nas/photos/icloud-sync/`
2. picture-pipeline watches this directory
3. New photos trigger processing pipeline
4. Originals moved to `/mnt/nas/photos/originals/YYYY/MM/DD/`
5. Thumbnails generated locally

---

### Option 2: Immich (Alternative)

**Tool**: Immich for sync + management

**Pros**:
- ✅ All-in-one (sync + management + UI)
- ✅ Mobile app for uploads
- ✅ Face recognition built-in
- ✅ Modern UI

**Cons**:
- ❌ Own database (not picture-pipeline source of truth)
- ❌ Less control over storage structure

**Integration**:
```python
# picture-pipeline reads Immich's storage
immich_storage = "/mnt/nas/immich/library"

# Import from Immich
for photo in scan_directory(immich_storage):
    if not exists_in_pipeline(photo.hash):
        import_to_pipeline(photo)
```

---

### Option 3: Hybrid (BEST OF BOTH)

Use **Docker iCloud backup** for sync + **Immich** as one consumer

**Flow**:
1. **iCloud → Docker container** (authoritative sync)
2. **Docker → picture-pipeline** (processing)
3. **picture-pipeline → NAS originals** (storage)
4. **NAS → Immich** (read-only external library)
5. **NAS → digiKam** (read-only)
6. **NAS → PhotoPrism** (read-only)

**Configuration**:
```yaml
# Immich: External library (read-only)
immich:
  external_libraries:
    - name: "Picture Pipeline"
      path: "/mnt/nas/photos/originals"
      scan_interval: "1h"
      read_only: true
```

---

## digiKam Integration

### Why digiKam is Important

- **Local editing** on NixOS workstation
- **Album organization**
- **Existing workflow**

### Integration Strategy

**digiKam configuration**:
```ini
# ~/.config/digikamrc
[General Settings]
Database Name=sqlite
Database Backend=SQLite
SQLite Database File=/mnt/nas/photos/digikam.db

[Album Settings]
Album Path=/mnt/nas/photos/originals
Album Hierarchy=Year/Month/Day

[Metadata Settings]
Read Metadata From Sidecars=true
Write Metadata To Sidecars=true
Sidecar Format=XMP
```

**Flow**:
1. digiKam scans `/mnt/nas/photos/originals/`
2. Reads XMP sidecars (generated by picture-pipeline)
3. Can edit/tag photos
4. Writes changes back to XMP
5. picture-pipeline re-imports XMP changes

**Thumbnail Strategy**:
```bash
# digiKam uses local thumbnails
ln -s ~/.local/share/pictures/thumbs/ ~/.local/share/digikam/thumbnails/picture-pipeline

# Or configure digiKam to use picture-pipeline thumbs
```

---

## Smart Storage: Implementation

### 1. Thumbnail Generation (On Import)

```python
from PIL import Image

def generate_thumbnails(original_path: Path, sha256: str):
    """Generate all thumbnail sizes."""
    sizes = {
        'tiny': (150, 150),
        'small': (500, 500),
        'medium': (1920, 1080)
    }

    img = Image.open(original_path)

    for size_name, (width, height) in sizes.items():
        # Resize maintaining aspect ratio
        img.thumbnail((width, height), Image.Resampling.LANCZOS)

        # Save to local storage
        thumb_path = get_thumb_path(sha256, size_name)
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(thumb_path, quality=85, optimize=True)

    # Original to NAS
    nas_path = get_nas_path(sha256)
    nas_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(original_path, nas_path)
```

### 2. Cache Management (LRU)

```python
class PhotoCache:
    """LRU cache for full-resolution photos."""

    def __init__(self, max_size_gb: int = 50):
        self.max_size = max_size_gb * 1024 * 1024 * 1024
        self.cache_dir = Path("~/.local/share/pictures/cache/full").expanduser()
        self.access_log = {}  # {sha256: last_access_time}

    def get(self, sha256: str) -> Optional[Path]:
        """Get from cache, fetch from NAS if not present."""
        cache_path = self.cache_dir / sha256[:2] / f"{sha256}.jpg"

        if cache_path.exists():
            # Update access time
            self.access_log[sha256] = time.time()
            return cache_path

        # Fetch from NAS
        nas_path = get_nas_path(sha256)
        if nas_path.exists():
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(nas_path, cache_path)
            self.access_log[sha256] = time.time()

            # Check cache size, evict if needed
            self._evict_if_needed()

            return cache_path

        return None

    def _evict_if_needed(self):
        """Evict least recently used files if cache too large."""
        total_size = sum(f.stat().st_size for f in self.cache_dir.rglob("*.jpg"))

        if total_size > self.max_size:
            # Sort by access time, remove oldest
            sorted_files = sorted(
                self.access_log.items(),
                key=lambda x: x[1]
            )

            # Remove oldest 10%
            to_remove = sorted_files[:len(sorted_files) // 10]
            for sha256, _ in to_remove:
                cache_path = self.cache_dir / sha256[:2] / f"{sha256}.jpg"
                cache_path.unlink(missing_ok=True)
                del self.access_log[sha256]
```

### 3. Storage Configuration

```yaml
# config/storage.yaml
storage:
  # Local (SSD)
  local:
    base_path: "~/.local/share/pictures"
    thumbnails:
      tiny: 150
      small: 500
      medium: 1920
    cache:
      max_size_gb: 50  # Full-res cache limit
      ttl_days: 30     # Evict after 30 days

  # NAS (Network Storage)
  nas:
    base_path: "/mnt/nas/photos"
    originals: "originals/{year}/{month}/{day}"
    sidecars: "originals/{year}/{month}/{day}"
    backups: "backups/icloud-archive"

  # Sync source
  sync:
    method: "docker-icloud"  # or 'immich', 'rsync'
    watch_path: "/mnt/nas/photos/icloud-sync"
    poll_interval_seconds: 60

  # Tool integration
  tools:
    immich:
      enabled: true
      mode: "external_library"
      path: "/mnt/nas/photos/originals"
    photoprism:
      enabled: true
      mode: "symlink"
      path: "/mnt/nas/photos/originals"
    digikam:
      enabled: true
      mode: "direct"
      database: "/mnt/nas/photos/digikam.db"
      thumbnails: "shared"  # Use picture-pipeline thumbs
```

---

## Migration Plan

### Phase 1: Consolidation (Week 1)

1. **Backup everything**:
   ```bash
   rsync -av /current/photos/ /mnt/nas/photos/backup-$(date +%Y%m%d)/
   ```

2. **Stop redundant syncs**:
   - Disable iOS Photos Sync app
   - Disable Synology iCloud sync
   - Keep Docker iCloud backup running

3. **Set up picture-pipeline**:
   ```bash
   cd ~/Documents/mygit/picture-pipeline
   ./run.sh setup-storage  # Configure NAS paths
   ./run.sh import /mnt/nas/photos/backup-*/  # Import existing
   ```

### Phase 2: Thumbnail Generation (Week 2)

1. **Generate thumbnails for all existing photos**:
   ```bash
   ./run.sh generate-thumbs --all  # Background job
   ```

2. **Verify**:
   ```bash
   ./run.sh storage-stats
   # Output:
   # Total photos: 50,000
   # Local thumbnails: 50,000 (15 GB)
   # NAS originals: 50,000 (500 GB)
   # Cache: 500 photos (5 GB)
   ```

### Phase 3: Tool Integration (Week 3)

1. **Immich**: Point to NAS as external library
2. **digiKam**: Configure to use NAS + local thumbs
3. **PhotoPrism**: Scan NAS directory
4. **Damselfly**: Create symlinks

### Phase 4: Ongoing Sync (Week 4+)

1. **Docker iCloud** continuously syncs to `/mnt/nas/photos/icloud-sync/`
2. **picture-pipeline** watches and processes new photos
3. **All tools** automatically see new photos
4. **Local browsing** uses thumbnails (fast)
5. **Editing** fetches full-res on-demand

---

## Benefits of This Architecture

### 1. Single Source of Truth
- ✅ No confusion about which sync to trust
- ✅ One database with all metadata
- ✅ Centralized sidecar management

### 2. Fast Local Browsing
- ✅ 100% thumbnails locally (15-20 GB for 50k photos)
- ✅ Instant grid view, no NAS access
- ✅ Works offline (browsing only)

### 3. On-Demand Full Resolution
- ✅ Fetch only when editing
- ✅ Smart caching (LRU, 50 GB limit)
- ✅ No wasted local storage

### 4. Tool Flexibility
- ✅ Use any tool (Immich, digiKam, PhotoPrism)
- ✅ All see same data
- ✅ No vendor lock-in

### 5. iPhone Verification
- ✅ Every photo verified as iPhone/not
- ✅ Location tracking for Dawarich
- ✅ Legal proof of presence

---

## Next Steps

1. ✅ Choose sync method: **Docker iCloud backup**
2. Set up picture-pipeline with storage config
3. Import existing photo library
4. Generate thumbnails for all photos
5. Configure tools (Immich, digiKam, PhotoPrism)
6. Start continuous sync + processing
