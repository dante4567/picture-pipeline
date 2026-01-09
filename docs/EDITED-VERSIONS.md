# Edited Versions & File System Visibility

Handling edited photos from iPhone + making everything browsable in file managers.

---

## iPhone Edited Photos

### How iPhone Edits Work

When you edit a photo on iPhone:
```
Original: IMG_1234.HEIC (untouched)
Adjustments: IMG_1234.AAE (edit instructions)
Result: iPhone shows edited version, but original preserved
```

**AAE files** contain:
- Crop coordinates
- Exposure adjustments
- Filter applied
- Markup/drawings
- Date of edit

### icloudpd Handles This!

```bash
# icloudpd downloads BOTH original + edited
icloudpd --download-videos \
         --folder-structure {:%Y}/{:%Y-%m-%d} \
         --set-exif-datetime \
         --xmp-sidecar

# Result:
/mnt/nas-photos/icloudpd/2023/2023-04-09/
  IMG_1234.HEIC              # Original (untouched)
  IMG_1234_edited.HEIC       # Edited version (with adjustments applied)
  IMG_1234.AAE               # Adjustment metadata (optional to keep)
```

### picture-pipeline Import Strategy

```python
def import_photo_with_edits(source_dir: Path):
    """Import both original and edited versions."""

    # Find all photos with edits
    for heic_file in source_dir.glob("**/*.heic"):
        # Check for edited version
        edited_file = heic_file.with_stem(f"{heic_file.stem}_edited")

        # Import original
        original_hash = import_photo(heic_file, version="original")

        # Import edited (if exists)
        if edited_file.exists():
            edited_hash = import_photo(edited_file, version="edited")

            # Link them in database
            db.execute("""
                UPDATE photos.images
                SET edited_version_id = :edited_id,
                    has_edits = TRUE
                WHERE sha256_hash = :original_hash
            """, edited_id=edited_hash, original_hash=original_hash)

            # Store edit metadata from AAE (if available)
            aae_file = heic_file.with_suffix('.AAE')
            if aae_file.exists():
                edit_metadata = parse_aae_file(aae_file)
                db.execute("""
                    UPDATE photos.images
                    SET edit_metadata = :metadata
                    WHERE sha256_hash = :edited_hash
                """, metadata=json.dumps(edit_metadata), edited_hash=edited_hash)
```

### Storage Structure with Edits

```
/mnt/nas/photos/originals/
├── 2023/
│   ├── 2023-04/
│   │   ├── pictures/
│   │   │   ├── 75820de3.heic          # Original (READ-ONLY)
│   │   │   ├── 75820de3.xmp           # Metadata
│   │   │   ├── 75820de3_edited.heic   # Edited version (READ-ONLY)
│   │   │   ├── 75820de3_edited.xmp    # Edit metadata
│   │   │   │
│   │   │   ├── a61bb03b.heic          # Another original
│   │   │   └── a61bb03b.xmp           # (no edits for this one)
```

**Naming convention**:
- Original: `{hash}.heic`
- Edited: `{hash}_edited.heic`
- Both are READ-ONLY (chmod 444)

### Database Schema

```sql
ALTER TABLE photos.images ADD COLUMN edited_version_id INTEGER REFERENCES photos.images(id);
ALTER TABLE photos.images ADD COLUMN original_version_id INTEGER REFERENCES photos.images(id);
ALTER TABLE photos.images ADD COLUMN has_edits BOOLEAN DEFAULT FALSE;
ALTER TABLE photos.images ADD COLUMN edit_metadata JSONB;  -- AAE file contents

CREATE INDEX idx_images_edits ON photos.images(original_version_id, edited_version_id);
```

### Queries

```sql
-- Find all photos with edits
SELECT
    original.file_path AS original,
    edited.file_path AS edited,
    original.edit_metadata->>'adjustments' AS edits_applied
FROM photos.images original
JOIN photos.images edited ON edited.id = original.edited_version_id
WHERE original.has_edits = TRUE;

-- Show original + edited side-by-side
SELECT
    original.sha256_hash,
    original.file_path AS original_path,
    edited.file_path AS edited_path,
    original.date_taken,
    edited.aesthetic_score AS edited_score,
    original.aesthetic_score AS original_score
FROM photos.images original
LEFT JOIN photos.images edited ON edited.id = original.edited_version_id;
```

---

## File System Visibility

### Browsable Directory Structure

```
/mnt/nas/photos/originals/
├── 2017/
│   ├── 2017-11/
│   │   ├── pictures/
│   │   │   ├── ac411c8a.heic
│   │   │   ├── ac411c8a.xmp
│   │   │   ├── 2e29a2b2.heic
│   │   │   └── 2e29a2b2.xmp
│   │   └── videos/
│   │       ├── dbf5e076.mov
│   │       └── dbf5e076.xmp
│   └── 2017-12/
│       └── ...
├── 2018/
│   ├── 2018-01/
│   └── ...
└── 2025/
    └── 2025-01/
        ├── pictures/
        └── videos/
```

**Every file is a real file** on the file system, not hidden in a database!

### File Manager Access

**Linux (Nautilus, Dolphin, Thunar)**:
```bash
# Open in file manager
nautilus /mnt/nas/photos/originals/2023/2023-04/pictures/

# Browse with ls
ls -lh /mnt/nas/photos/originals/2023/2023-04/pictures/
# Shows:
# -r--r--r-- 4.2M 75820de3.heic
# -rw-r--r--  12K 75820de3.xmp
# -r--r--r-- 4.3M 75820de3_edited.heic
# -rw-r--r--  13K 75820de3_edited.xmp
```

**macOS (Finder)**:
```bash
# Open in Finder
open /Volumes/NAS/photos/originals/2023/2023-04/pictures/

# Browse files directly, thumbnails visible in Finder
# Double-click to open in Preview, Photos, etc.
```

**Windows (Explorer)**:
```
\\NAS\photos\originals\2023\2023-04\pictures\

# Browse normally in Windows Explorer
# Thumbnails visible (if HEIC codec installed)
# Right-click → Properties shows EXIF metadata
```

### Thumbnail Symlinks (Optional)

For even faster file manager browsing, create symlinks to thumbnails:

```bash
# Create thumbnail symlinks alongside originals
for file in /mnt/nas/photos/originals/**/**/*.heic; do
    hash=$(basename "$file" .heic)
    thumb=~/.local/share/pictures/thumbs/small/${hash}.jpg

    if [ -f "$thumb" ]; then
        # Create symlink: .thumb.jpg alongside .heic
        ln -sf "$thumb" "${file%.heic}.thumb.jpg"
    fi
done

# Result:
/mnt/nas/photos/originals/2023/2023-04/pictures/
  75820de3.heic         # Original (4 MB)
  75820de3.thumb.jpg    # → Symlink to thumbnail (100 KB)
  75820de3.xmp          # Metadata
```

**Benefit**: File managers show thumbnails instantly (from symlink), no need to generate on-the-fly!

### Copying Files Preserves Everything

```bash
# Copy a photo (original + XMP travel together)
cp /mnt/nas/photos/originals/2023/2023-04/pictures/75820de3.* /tmp/

# Result:
/tmp/75820de3.heic          # Original photo
/tmp/75820de3.xmp           # All metadata
/tmp/75820de3_edited.heic   # Edited version (if exists)
/tmp/75820de3_edited.xmp    # Edit metadata
```

**All metadata travels with the photo!** (XMP sidecar standard)

### Archive Formats

```bash
# Create archive with year structure
tar -czf 2023-photos.tar.gz /mnt/nas/photos/originals/2023/

# Extract preserves structure
tar -xzf 2023-photos.tar.gz
# Result: Exact same YYYY/YYYY-MM/pictures/ structure restored
```

---

## Tool Integration with File System

### digiKam (Direct File Access)

```
digiKam Settings:
  Album Path: /mnt/nas/photos/originals/
  Album Hierarchy: YYYY/YYYY-MM/pictures|videos
  Read/Write XMP: YES
  Thumbnail Path: ~/.local/share/pictures/thumbs/  (shared!)
```

**Benefit**: digiKam sees files directly, no import needed. Changes to XMP visible immediately.

### PhotoPrism (Index File System)

```yaml
# docker-compose.yml
photoprism:
  volumes:
    - /mnt/nas/photos/originals:/photoprism/originals:ro  # READ-ONLY!
```

**Benefit**: PhotoPrism indexes existing files, no duplication. Can't modify originals (read-only mount).

### Immich (External Library)

```
Immich:
  External Library: /mnt/nas/photos/originals/
  Watch for changes: YES
  Import: NO (just index)
```

**Benefit**: Immich sees all photos without duplicating storage.

### Command Line

```bash
# Find all photos with person "daughter"
find /mnt/nas/photos/originals/ -name "*.xmp" -exec grep -l "daughter" {} \;

# Count photos per year
du -sh /mnt/nas/photos/originals/*/

# Find high-quality photos (aesthetic_score > 8.0)
grep -l "AestheticScore>8" /mnt/nas/photos/originals/**/**/*.xmp
```

---

## Backup & Migration

### Rsync to Backup Drive

```bash
# Incremental backup (preserves timestamps, permissions, symlinks)
rsync -avh \
  --progress \
  /mnt/nas/photos/originals/ \
  /mnt/backup/photos-$(date +%Y%m%d)/

# Restore (exact same structure)
rsync -avh /mnt/backup/photos-20260109/ /mnt/nas/photos/originals/
```

### Cloud Backup (rclone)

```bash
# Sync to Backblaze B2 / S3 / Google Drive
rclone sync \
  /mnt/nas/photos/originals/ \
  remote:photos-backup/ \
  --progress \
  --exclude "*.thumb.jpg"  # Skip thumbnail symlinks
```

### Export for Sharing

```bash
# Export year with thumbnails
./run.sh export-year \
  --year 2023 \
  --with-thumbnails \
  --with-xmp \
  --output /tmp/2023-photos/

# Result: Portable directory, all metadata included
/tmp/2023-photos/
  2023/
    2023-04/
      pictures/
        75820de3.heic
        75820de3.xmp
        75820de3.thumb.jpg  # Converted (not symlink)
```

---

## Summary

### ✅ Edited Versions

1. **Both imported**: Original + edited versions (if photo was edited on iPhone)
2. **Linked in database**: `edited_version_id` links them
3. **Named clearly**: `{hash}.heic` (original), `{hash}_edited.heic` (edited)
4. **AAE metadata preserved**: Edit history stored in database
5. **Both visible in apps**: digiKam, PhotoPrism show both versions

### ✅ File System Visibility

1. **Real files**: Everything is a real file on disk, not hidden in database
2. **Browsable structure**: YYYY/YYYY-MM/pictures|videos hierarchy
3. **File manager access**: Nautilus, Finder, Explorer can browse directly
4. **XMP travels with photo**: Copy .heic → .xmp comes along
5. **Thumbnail symlinks**: Optional fast preview in file managers
6. **Backup-friendly**: Standard directory structure, rsync/rclone work
7. **Tool-agnostic**: Any app can access files directly

**You can delete picture-pipeline entirely** and still have all your photos organized in file system with XMP metadata!

---

*Next: Implement edited version detection and import*
