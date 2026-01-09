# Storage Tiers & Format Optimization

Multi-tier storage strategy + format conversion for easy usage.

---

## Storage Tiers

### Tier 1: Hot (NVMe SSD - Local)
**Purpose**: Immediate access, browsing, editing
**Contents**:
- Thumbnails (all sizes)
- Recent photos (last 3 months)
- High aesthetic score photos (>8.0)
- Screenshots (organized, renamed)

**Storage**: `~/.local/share/pictures/` (~50-100 GB)

---

### Tier 2: Warm (HDD - NAS)
**Purpose**: Active library, frequently accessed
**Contents**:
- Current year originals
- Last 2 years in easily-used formats (JPG, H.264)
- XMP sidecars
- Face recognition database

**Storage**: `/mnt/nas/photos/active/` (~500 GB - 1 TB)

---

### Tier 3: Cold (External/Cloud - Archive)
**Purpose**: Long-term archive, rarely accessed
**Contents**:
- Older photos (>2 years) in original format
- RAW files
- Duplicates (for redundancy)
- Original Apple formats (HEIC, HEVC, ProRes)

**Storage**: `/mnt/nas/photos/archive/` or cloud (~2-5 TB)

---

## Format Conversion Strategy

### Goal: Easily Used Formats

**Problem**: Apple uses efficient but less-compatible formats:
- **HEIC** (photos) - Not supported by many tools
- **HEVC/H.265** (videos) - Requires hardware decoding
- **ProRAW** - Huge files, limited software support
- **Live Photos** - MOV + JPG pair, confusing

**Solution**: Convert to universal formats for active storage

---

### Photo Conversion Rules

| Source Format | Active Format | Cold Format | Notes |
|---------------|---------------|-------------|-------|
| HEIC | JPG (quality 95) | HEIC (original) | Universal compatibility |
| ProRAW | DNG + JPG preview | ProRAW (original) | DNG for editing, JPG for viewing |
| PNG (screenshot) | PNG (optimized) | PNG (original) | Keep PNG, optimize size |
| TIFF | JPG | TIFF (original) | Convert for web viewing |

### Video Conversion Rules

| Source Format | Active Format | Cold Format | Notes |
|---------------|---------------|-------------|-------|
| HEVC/H.265 | H.264 (high quality) | HEVC (original) | H.264 for compatibility |
| ProRes | H.264 (high bitrate) | ProRes (original) | Smaller, playable everywhere |
| MOV (Live Photo) | MP4 (extract video) | MOV (original) | Separate video from Live Photo |
| AVI, MKV | MP4 (H.264) | Original format | Standardize to MP4 |

---

## Implementation

### Conversion Pipeline

```python
from PIL import Image
import pillow_heif
import ffmpeg

class FormatConverter:
    """Convert media to easily-used formats."""

    def convert_photo(self, source_path: Path, quality: int = 95) -> Path:
        """Convert photo to JPG."""
        if source_path.suffix.lower() == '.heic':
            # HEIC → JPG
            heif_file = pillow_heif.read_heif(source_path)
            image = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw"
            )
            output_path = source_path.with_suffix('.jpg')
            image.save(output_path, quality=quality, optimize=True)
            return output_path

        elif source_path.suffix.lower() == '.png':
            # PNG optimization
            image = Image.open(source_path)
            output_path = source_path.with_stem(f"{source_path.stem}_opt")
            image.save(output_path, optimize=True, compress_level=9)
            return output_path

        else:
            # Already in good format
            return source_path

    def convert_video(self, source_path: Path, codec: str = 'libx264') -> Path:
        """Convert video to H.264 MP4."""
        output_path = source_path.with_suffix('.mp4')

        ffmpeg.input(source_path).output(
            str(output_path),
            vcodec=codec,
            crf=23,  # Quality (18-28, lower = better)
            preset='medium',
            acodec='aac',
            audio_bitrate='192k'
        ).overwrite_output().run()

        return output_path
```

---

## Storage Tier Migration

### Auto-Migration Rules

1. **Hot → Warm** (after 3 months):
   ```python
   if photo.age_days > 90:
       move_to_warm(photo)
       keep_thumbnail(photo)  # Keep thumbnail on hot
   ```

2. **Warm → Cold** (after 2 years):
   ```python
   if photo.age_days > 730:
       # Keep easily-used format on warm
       move_original_to_cold(photo)
       # Example: Keep JPG on warm, move HEIC to cold
   ```

3. **Exceptions** (always keep on hot/warm):
   - High aesthetic score (>8.0)
   - Photos with family faces
   - Recently edited
   - Marked as favorite

### Migration Script

```python
def migrate_photos():
    """Migrate photos between storage tiers."""

    # Hot → Warm (>3 months)
    old_photos = db.query(Photo).filter(
        Photo.date_taken < datetime.now() - timedelta(days=90),
        Photo.storage_tier == 'hot'
    ).all()

    for photo in old_photos:
        # Keep thumbnail on hot
        if not photo.thumbnail_exists:
            generate_thumbnail(photo)

        # Move full-res to warm
        warm_path = f"/mnt/nas/photos/active/{photo.date_path}/{photo.sha256}.jpg"
        shutil.move(photo.path, warm_path)
        photo.path = warm_path
        photo.storage_tier = 'warm'
        db.commit()

    # Warm → Cold (>2 years, low importance)
    archive_candidates = db.query(Photo).filter(
        Photo.date_taken < datetime.now() - timedelta(days=730),
        Photo.storage_tier == 'warm',
        Photo.aesthetic_score < 7.0,
        ~Photo.has_family_faces
    ).all()

    for photo in archive_candidates:
        # Move original to cold
        cold_path = f"/mnt/nas/photos/archive/{photo.date_taken.year}/{photo.sha256}{photo.original_extension}"
        shutil.move(find_original(photo), cold_path)

        # Keep easily-used version on warm
        if photo.original_format == 'HEIC':
            # Keep JPG on warm, move HEIC to cold
            pass

        photo.storage_tier = 'cold'
        photo.cold_storage_path = cold_path
        db.commit()
```

---

## Screenshot Management

### Problem
Screenshots scattered across:
- iPhone (Photos app)
- Desktop (~/Desktop/, ~/Downloads/)
- Work laptop
- Cloud sync folders

Names like: `Screenshot 2024-06-15 at 10.23.45 AM.png` (useless)

### Solution: Automatic Screenshot Pipeline

```
Sources:
  • iPhone iCloud
  • Desktop screenshot folder
  • Laptop screenshot folder
         ↓
   Detection (is it a screenshot?)
         ↓
   OCR + Context Extraction
         ↓
   Intelligent Renaming
         ↓
   Organized Storage
```

---

### Screenshot Detection

```python
def is_screenshot(photo: Photo) -> bool:
    """Detect if photo is a screenshot."""

    # Check filename patterns
    filename_patterns = [
        r'screenshot',
        r'screen shot',
        r'capture d\'écran',  # French
        r'bildschirmfoto',    # German
        r'SCR_\d+',           # Some tools
    ]

    filename_lower = photo.filename.lower()
    for pattern in filename_patterns:
        if re.search(pattern, filename_lower):
            return True

    # Check EXIF for screenshot indicators
    if not photo.exif_data.get('Make'):  # No camera make
        if photo.exif_data.get('Software'):
            # Screenshot software indicators
            screenshot_software = [
                'screenshots',
                'snagit',
                'lightshot',
                'greenshot'
            ]
            software_lower = photo.exif_data['Software'].lower()
            if any(s in software_lower for s in screenshot_software):
                return True

    # Check resolution (common screen resolutions)
    common_resolutions = [
        (1920, 1080), (2560, 1440), (3840, 2160),  # Desktop
        (1284, 2778), (1170, 2532), (1179, 2556),  # iPhone
        (1440, 3200), (1440, 2960),                 # Android
    ]

    width, height = photo.width, photo.height
    if (width, height) in common_resolutions or (height, width) in common_resolutions:
        # High probability it's a screenshot
        return True

    return False
```

---

### OCR + Context Extraction

```python
import pytesseract
from PIL import Image

def extract_screenshot_context(photo_path: Path) -> dict:
    """Extract text and context from screenshot."""

    # Use vision LLM (better than traditional OCR)
    with open(photo_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()

    response = litellm.completion(
        model="llama-4-scout-17b",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": """
                Analyze this screenshot and extract:
                1. Main topic/purpose (1-3 words)
                2. Application/website name (if visible)
                3. Key text content (summary in 5-10 words)

                Format as JSON:
                {
                    "topic": "...",
                    "app": "...",
                    "content": "..."
                }
                """},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
            ]
        }]
    )

    return json.loads(response.choices[0].message.content)
```

---

### Intelligent Renaming

```python
def rename_screenshot(photo: Photo, context: dict) -> str:
    """Generate meaningful screenshot name."""

    # Format: YYYYMMDD_HHMM_<app>_<topic>_<short_desc>.png
    timestamp = photo.date_taken.strftime("%Y%m%d_%H%M")
    app = context['app'].replace(' ', '_') if context['app'] else 'unknown'
    topic = context['topic'].replace(' ', '_')

    # Clean content for filename
    content = context['content'][:30]  # Max 30 chars
    content = re.sub(r'[^\w\s-]', '', content)  # Remove special chars
    content = re.sub(r'\s+', '_', content)      # Spaces to underscores

    new_name = f"{timestamp}_{app}_{topic}_{content}.png"

    return new_name
```

**Examples**:

| Original Name | New Name |
|---------------|----------|
| `Screenshot 2024-06-15 at 10.23.45 AM.png` | `20240615_1023_Safari_Recipe_Chocolate_Cake_Instructions.png` |
| `IMG_0123.PNG` | `20240615_1430_Settings_WiFi_Network_Configuration.png` |
| `Capture d'écran 2024-06-15 à 14.30.45.png` | `20240615_1430_Messages_Chat_Daughter_School_Pickup.png` |

---

### Screenshot Organization

```
~/.local/share/pictures/screenshots/
├── 2024/
│   ├── 06/
│   │   ├── work/
│   │   │   ├── 20240615_1000_Slack_Meeting_Notes.png
│   │   │   └── 20240615_1430_Email_Project_Update.png
│   │   ├── personal/
│   │   │   ├── 20240615_1200_Safari_Recipe_Dinner.png
│   │   │   └── 20240615_1500_Messages_Family_Chat.png
│   │   └── reference/
│   │       ├── 20240615_1600_Documentation_API_Reference.png
│   │       └── 20240615_1700_Settings_Config_Guide.png
```

### Auto-Categorization

```python
def categorize_screenshot(context: dict) -> str:
    """Categorize screenshot by content."""

    # Use LLM
    prompt = f"""
    Categorize this screenshot into one of:
    - work (emails, Slack, meetings, docs)
    - personal (recipes, shopping, messages, social)
    - reference (docs, tutorials, settings, configs)
    - finance (banking, invoices, receipts)
    - travel (bookings, tickets, maps)

    App: {context['app']}
    Topic: {context['topic']}
    Content: {context['content']}

    Return only the category name.
    """

    response = litellm.completion(
        model="openai/chat-fast",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()
```

---

## Screenshot Sync Configuration

### Auto-Sync from All Devices

```yaml
# config/screenshot-sync.yaml
screenshot_sync:
  sources:
    - name: "iPhone"
      method: "icloud"
      path: "/mnt/nas/photos/icloud-sync/Screenshots"
      enabled: true

    - name: "Desktop"
      method: "watch_folder"
      path: "~/Desktop"
      pattern: "*.png"
      enabled: true

    - name: "Laptop"
      method: "rsync"
      host: "laptop.local"
      path: "~/Desktop"
      enabled: true

  processing:
    detect_screenshots: true
    extract_context: true
    auto_rename: true
    auto_categorize: true
    delete_original: false  # Keep original for safety

  storage:
    destination: "~/.local/share/pictures/screenshots"
    organize_by:
      - year
      - month
      - category
```

---

## Storage Summary

### By Tier

| Tier | Storage Type | Capacity | Contents | Access Speed |
|------|--------------|----------|----------|--------------|
| Hot | NVMe SSD (local) | 100 GB | Thumbnails, recent, screenshots | <10ms |
| Warm | HDD (NAS) | 1 TB | Active library (JPG, H.264) | 50-100ms |
| Cold | HDD/Cloud (archive) | 5 TB | Old originals (HEIC, HEVC, RAW) | 1-10s |

### By Format

| Format | Tier | Size | Compatibility |
|--------|------|------|---------------|
| Thumbnails (JPG) | Hot | 50 MB | ★★★★★ |
| JPG (converted) | Warm | 300 GB | ★★★★★ |
| H.264 video | Warm | 500 GB | ★★★★★ |
| HEIC (original) | Cold | 200 GB | ★★☆☆☆ |
| HEVC video | Cold | 1 TB | ★★★☆☆ |
| RAW | Cold | 500 GB | ★☆☆☆☆ |

---

## Benefits

### 1. Fast Access
- ✅ Thumbnails local (instant browsing)
- ✅ Recent photos on SSD (quick editing)
- ✅ Warm storage on NAS (network fast)

### 2. Universal Compatibility
- ✅ JPG photos work everywhere
- ✅ H.264 videos play on any device
- ✅ No "format not supported" errors

### 3. Cost Optimization
- ✅ Expensive SSD for hot data only
- ✅ Cheap HDD for archive
- ✅ Original formats preserved in cold storage

### 4. Screenshot Management
- ✅ Auto-sync from all devices
- ✅ Meaningful names (no more "Screenshot 2024...")
- ✅ Organized by category
- ✅ Searchable by content

---

## Implementation Priority

### Phase 1: Storage Tiers (Week 1)
- Set up hot/warm/cold directories
- Implement format conversion
- Test HEIC → JPG, HEVC → H.264

### Phase 2: Migration (Week 2)
- Script to migrate old photos
- Auto-migration rules
- Verify all originals preserved

### Phase 3: Screenshot Pipeline (Week 3)
- Auto-sync from all devices
- OCR + context extraction
- Intelligent renaming
- Auto-categorization

### Phase 4: Optimization (Week 4)
- Monitor access patterns
- Adjust tier boundaries
- Optimize conversion quality
- Cache tuning
