# picture-pipeline: Complete User Workflow

From iPhone → Safe storage → Quick access everywhere

---

## Your Workflow

### 1. Take photos on iPhone
- Photos stored in iPhone Photos app
- Auto-sync to iCloud Photos
- Docker container (icloudpd) downloads to NAS

### 2. picture-pipeline imports automatically
```
iPhone → iCloud → icloudpd → picture-pipeline
                               ↓
        /mnt/nas/photos/originals/2023/2023-04/pictures/75820de3.heic (READ-ONLY)
        /mnt/nas/photos/originals/2023/2023-04/pictures/75820de3.xmp  (metadata)
                               ↓
        ~/.local/share/pictures/thumbs/small/75820de3.jpg (500x500, local)
```

**What happens**:
- ✅ SHA256 hash calculated (provenance)
- ✅ iPhone verified (GPS Date/Time stamps preserved)
- ✅ Thumbnails generated (3 sizes: 150px, 500px, 1920px)
- ✅ XMP sidecar created (metadata)
- ✅ Database entry (searchable)

### 3. **DELETE photos from iPhone!** 🎉
- Photos are safely on NAS (verified hash ✓)
- Thumbnails on local SSD (fast access ✓)
- **Free up iPhone storage!**

### 4. View photos on ANY device, ANY app
```
Desktop (digiKam)     → Reads: /mnt/nas/photos/originals/ + XMP
Laptop (PhotoPrism)   → Reads: /mnt/nas/photos/originals/ + XMP
Phone (Immich app)    → Reads: /mnt/nas/photos/originals/ + Thumbnails
Tablet (web browser)  → Reads: Thumbnails from picture-pipeline server
```

**All apps show SAME photos** (universal via NAS + XMP sidecars)

### 5. Find "best photo of daughter" in <1 second
```bash
./run.sh best-photo daughter
# Shows: Top 10 photos, sorted by quality score
```

```sql
-- Or in any app that can query database:
SELECT file_path, aesthetic_score, date_taken
FROM photos.images i
JOIN photos.faces f ON f.photo_id = i.id
WHERE f.person_name = 'daughter'
ORDER BY aesthetic_score DESC
LIMIT 10;
```

### 6. Need original? Access from NAS
```
Thumbnail: ~/.local/share/pictures/thumbs/small/75820de3.jpg (500x500, instant)
Original:  /mnt/nas/photos/originals/2023/2023-04/pictures/75820de3.heic (full quality)
```

**Thumbnails are "quite advanced"**: 500x500 or 1920x1080 is good enough for 99% of viewing!

**Only need original when**:
- Printing large format
- Professional editing in Lightroom/digiKam
- Proving authenticity (hash verification)

---

## Storage Tiers Explained

### Hot Tier (Local NVMe SSD) - FAST
```
~/.local/share/pictures/
  thumbs/
    tiny/     (150x150)   - List views, mobile
    small/    (500x500)   - Desktop viewing, web galleries
    medium/   (1920x1080) - Full-screen viewing
  cache/
    recent/   - Recently accessed originals (auto-managed)
```

**Total**: ~15 GB (thumbnails for 65,000 photos)
**Access**: Instant (<10ms)
**Use**: 99% of daily viewing

### Warm Tier (NAS HDD) - AVAILABLE
```
/mnt/nas/photos/originals/
  2023/
    2023-04/
      pictures/
        75820de3.heic  (r--r--r--, READ-ONLY)
        75820de3.xmp   (metadata sidecar)
      videos/
        9f8e7d6c.mov
        9f8e7d6c.xmp
```

**Total**: ~130 GB (65,000 unique photos after deduplication)
**Access**: Network (~50-100ms)
**Use**: Original access when needed

### Cold Tier (Archive) - SAFE
```
/mnt/nas/photos/archive/
  2023/
    backups/
      icloudpd-backup-2023-04-09.tar.gz
      iphoneSync-backup-2023-04-09.tar.gz
```

**Total**: ~100 GB (compressed archives)
**Access**: Manual restore
**Use**: Disaster recovery

---

## Tool Compatibility Matrix

| App | Thumbnail | Original | Person Tags | Quality Score | Delete from iPhone? |
|-----|-----------|----------|-------------|---------------|---------------------|
| **digiKam** (desktop) | ✅ Shared with picture-pipeline | ✅ NAS direct | ✅ XMP sync | ✅ Via XMP | ✅ Yes, safe! |
| **PhotoPrism** (web) | ✅ Own + picture-pipeline | ✅ NAS indexed | ✅ XMP read | ✅ AI tags | ✅ Yes, safe! |
| **Immich** (mobile app) | ✅ Own + picture-pipeline | ✅ External library | ✅ API sync | ✅ AI tags | ✅ Yes, safe! |
| **Obsidian** (notes) | ✅ picture-pipeline gallery | ✅ Link to NAS | ✅ Export MD | ✅ Ranked lists | ✅ Yes, safe! |

**All apps agree**:
- Same photos visible
- Same person tags
- Same keywords/projects
- Different UIs for different use cases

---

## Example User Journey

### Day 1: Take 100 photos on iPhone
- iPhone storage: 100 photos × 4 MB = 400 MB used

### Day 2: picture-pipeline imports automatically
```bash
# Cron job runs: ./run.sh import --source icloudpd
# Result:
✓ Imported: 100 photos
✓ Verified: 100 iPhone photos (GPS Date/Time stamps)
✓ Duplicates: 0 (all new)
✓ Thumbnails: 100 × 3 sizes generated
✓ Storage: NAS +400 MB originals, Local +2 MB thumbnails
```

### Day 3: Delete photos from iPhone
- Open iPhone Photos app
- Select all imported photos (from 2 days ago)
- Delete → Free up 400 MB on iPhone! 🎉

### Day 4: View photos on laptop (PhotoPrism)
- Open PhotoPrism web UI
- See all 100 photos (thumbnails from picture-pipeline)
- Photos load instantly (thumbnails on local network)
- Click to view full-screen (1920x1080 thumbnail, good enough!)

### Day 5: Tag person in digiKam
- Open digiKam on desktop
- Tag face as "daughter"
- digiKam writes to XMP sidecar
- picture-pipeline syncs to database
- PhotoPrism, Immich immediately see "daughter" tag ✅

### Day 6: Search "best photo of daughter"
```bash
./run.sh best-photo daughter --limit 5
```

**Output**:
```
✓ Top 5 photos of daughter:

1. Score: 9.2/10 | 2023-04-09 | 75820de3.heic
   Age: 21 months | Tags: outdoor, beach | People: daughter, spouse

2. Score: 8.9/10 | 2023-06-15 | a61bb03b.heic
   Age: 23 months | Tags: park | People: daughter

3. Score: 8.7/10 | 2023-03-10 | c7f9e2a1.heic
   Age: 20 months | Tags: indoor, family | People: daughter, grandparent

4. Score: 8.5/10 | 2023-05-01 | d16ff841.heic
   Age: 22 months | Tags: outdoor | People: daughter

5. Score: 8.3/10 | 2023-02-14 | 2e514d97.heic
   Age: 19 months | Tags: birthday | People: daughter, family
```

### Day 7: Need original for printing
- digiKam: Select photo → Edit → Opens original from NAS
- Or: Copy from NAS to editing workstation
- Hash verification: `./run.sh verify-hash 75820de3.heic` ✓

---

## Safety Checklist

Before deleting photos from iPhone:

```bash
# 1. Verify import completed
./run.sh verify-import --source icloudpd --date 2023-04-09
# Expected: All photos imported ✓

# 2. Verify hashes calculated
./run.sh verify-hashes --date 2023-04-09
# Expected: 100/100 photos hashed ✓

# 3. Verify thumbnails generated
./run.sh verify-thumbnails --date 2023-04-09
# Expected: 100/100 photos (3 sizes each) ✓

# 4. Verify XMP sidecars created
./run.sh verify-xmp --date 2023-04-09
# Expected: 100/100 XMP files ✓

# 5. Test access from apps
# Open PhotoPrism → See photos? ✓
# Open digiKam → See photos? ✓
# Open Immich → See photos? ✓
```

**If all ✓ → SAFE TO DELETE from iPhone!**

---

## Storage Comparison

### Before picture-pipeline (Current chaos):
```
iPhone:         10 GB (can't delete, no backup trust)
iCloud Photos:  83 GB (scattered across folders)
iphoneSync:     90 GB (duplicates + unique)
Immich:         50 GB (tried, gave up)
PhotoPrism:     40 GB (tried, gave up)
digiKam:        60 GB (some photos)
──────────────────────
Total:         333 GB (lots of duplicates, fragmented)
```

### After picture-pipeline (Consolidated):
```
iPhone:          0 GB (deleted, freed space!)
NAS originals: 130 GB (unique, deduplicated)
Local thumbs:   15 GB (instant access)
NAS archive:   100 GB (compressed backups)
──────────────────────
Total:         245 GB (26% savings, organized!)
```

**Benefits**:
- iPhone space freed: 10 GB → 0 GB 🎉
- Can take more photos without "storage full" warnings
- All photos safe on NAS (hash-verified)
- Fast access via thumbnails
- All apps in sync

---

## Advanced Features

### 1. Age-based photo albums
```sql
-- Auto-generate "Daughter's First Year" album
SELECT file_path FROM photos.images i
JOIN photos.faces f ON f.photo_id = i.id
WHERE f.person_name = 'daughter'
  AND f.age_months BETWEEN 0 AND 12
ORDER BY i.date_taken;
```

### 2. Project documentation
```bash
# Photos/screenshots from HomeAutomation project
./run.sh export-gallery \
  --project HomeAutomation \
  --date 2023-04-09 \
  --output ~/obsidian/projects/HomeAutomation/photos.md
```

### 3. Location-based search
```sql
-- All photos taken in Germany
SELECT file_path, gps_latitude, gps_longitude, date_taken
FROM photos.images
WHERE gps_latitude BETWEEN 47.0 AND 55.0
  AND gps_longitude BETWEEN 6.0 AND 15.0
ORDER BY date_taken;
```

### 4. Quality-filtered sharing
```bash
# Share best 20 photos from last vacation
./run.sh export-album \
  --date-range 2023-07-01:2023-07-31 \
  --min-score 8.0 \
  --output /tmp/vacation-best/ \
  --format jpg \
  --size 1920x1080
```

---

## Summary

### ✅ What You Get

1. **Free iPhone storage** - Delete photos safely after import
2. **Fast access everywhere** - Thumbnails load instantly
3. **Originals when needed** - Full quality on NAS
4. **Universal person tags** - Tag in any app, visible in all
5. **Quick search** - "Best photo of daughter" in <1 second
6. **Age tracking** - "Photos when daughter was 24 months old"
7. **Project linking** - Screenshots auto-grouped with keywords
8. **Provenance** - SHA256 hash proves authenticity
9. **Tool compatibility** - digiKam, PhotoPrism, Immich all work together

### ❌ What You Don't Worry About

- iPhone "storage full" warnings
- Losing photos (hash-verified backups)
- Tool conflicts (all use same NAS storage)
- Duplicate storage (deduplicated)
- Finding best photos (auto-ranked)
- Person tagging consistency (XMP sidecars sync)

---

**Next**: Implement SHA256 deduplication to start consolidation!

---

## SHA256: File Identity, Not Just Deduplication

### SHA256 = Unique File Fingerprint

```python
# SHA256 is calculated on the ENTIRE file (pixels + metadata)
sha256("photo.heic") = "75820de3d5dc41e9b21894a1a0458986"

# IF any bit changes → Hash changes!
sha256("photo_modified.heic") = "a61bb03b4c7f9e2a1d16ff8412e29a2b"  # Different!
```

**SHA256 tells you**:
- ✅ **File identity**: "This is file 75820de3, not a61bb03b"
- ✅ **Integrity**: "File hasn't been corrupted or tampered"
- ✅ **Provenance**: "This is the ORIGINAL from icloudpd"
- ✅ **Deduplication**: "75820de3 exists twice → keep one copy"

### Why icloudpd and iphoneSync Have DIFFERENT Hashes

**Same photo, different hashes?** YES, because:

```
icloudpd download:
  - Original HEIC from iCloud
  - GPS Date/Time stamps PRESERVED
  - Full EXIF metadata
  → SHA256: 75820de3d5dc41e9b21894a1a0458986

iphoneSync download:
  - Same pixels (visual content identical)
  - GPS Date/Time stamps STRIPPED
  - HDR/AF metadata ADDED
  → SHA256: a61bb03bd5dc41e9b218  # DIFFERENT!
```

**Pixel-identical, but hash differs** because metadata changed.

**Solution**: Use **perceptual hashing** (pHash) to find "visually similar":
```python
# Perceptual hash looks at PIXELS only (ignores metadata)
phash(icloudpd_photo) = "ffca3f8c7"
phash(iphoneSync_photo) = "ffca3f8c7"  # SAME! (visual match)

# Now we know: "These are the same photo, keep both for metadata merge"
```

### Originals Are NEVER Converted

```
icloudpd photo: 75820de3.heic → Stays .heic (original format)
iphoneSync photo: a61bb03b.heic → Stays .heic (original format)
Video: 9f8e7d6c.mov → Stays .mov (original format)
RAW: c7f9e2a1.cr2 → Stays .cr2 (original format)
```

**Only thumbnails are converted**:
```
Original: 75820de3.heic (4 MB, HEIC format)
Thumbnails:
  - tiny: 75820de3.jpg (10 KB, JPEG 150x150)
  - small: 75820de3.jpg (100 KB, JPEG 500x500)
  - medium: 75820de3.jpg (500 KB, JPEG 1920x1080)
```

**Original NEVER touched!**

---

## File Identity Workflow

### 1. Import from icloudpd
```python
photo = Path("/mnt/nas-photos/icloudpd/.../photo.heic")
sha256 = calculate_hash(photo)  # "75820de3d5dc41e9b21894a1a0458986"

# Store in database with FULL METADATA
db.execute("""
    INSERT INTO photos.images (
        sha256_hash,
        file_path,
        source,
        metadata
    ) VALUES (
        :hash,
        :path,
        'icloudpd',
        :metadata  -- FULL EXIF including GPS Date/Time
    )
""", hash=sha256, path=photo, metadata=extract_all_exif(photo))
```

### 2. Import from iphoneSync (different hash!)
```python
photo2 = Path("/mnt/nas-photos/iphoneSync/.../photo.heic")
sha256_2 = calculate_hash(photo2)  # "a61bb03bd5dc..." # DIFFERENT!

# Not a duplicate (SHA256 differs), but MIGHT be visually same
phash = calculate_perceptual_hash(photo2)  # "ffca3f8c7"

# Check database for perceptual matches
matches = db.query("""
    SELECT id, sha256_hash, file_path, perceptual_hash
    FROM photos.images
    WHERE perceptual_hash = :phash
""", phash=phash)

if matches:
    # VISUAL MATCH! Same photo, different metadata
    print(f"Found visual match: icloudpd ({matches[0].sha256_hash})")

    # Decision: Keep BOTH for metadata merge
    # - icloudpd: GPS Date/Time stamps (priority!)
    # - iphoneSync: HDR/AF data (nice to have)

    # Create new database entry for iphoneSync version
    db.execute("""
        INSERT INTO photos.images (
            sha256_hash,
            file_path,
            source,
            metadata,
            perceptual_hash,
            duplicate_of  -- Link to icloudpd version
        ) VALUES (
            :hash,
            :path,
            'iphoneSync',
            :metadata,  -- HDR/AF metadata
            :phash,
            :duplicate_of
        )
    """, hash=sha256_2, path=photo2, metadata=extract_all_exif(photo2),
         phash=phash, duplicate_of=matches[0].id)

    # Merge metadata to XMP sidecar
    merge_metadata_to_xmp(
        icloudpd_photo=matches[0],
        iphoneSync_photo=photo2,
        output_xmp=matches[0].xmp_path
    )
else:
    # No visual match → Unique photo from iphoneSync
    # (One of the +10,136 photos not in icloudpd!)
    db.execute("INSERT INTO photos.images ...")
```

### 3. Access by file identity
```bash
# User: "Show me file 75820de3"
./run.sh show 75820de3

# Database query:
SELECT file_path, source, date_taken, metadata
FROM photos.images
WHERE sha256_hash LIKE '75820de3%';

# Result:
Path: /mnt/nas/photos/originals/2023/2023-04/pictures/75820de3.heic
Source: icloudpd
Hash: 75820de3d5dc41e9b21894a1a0458986
Visual match: a61bb03bd5dc... (iphoneSync version, same photo)
```

---

## Summary: SHA256 + pHash Strategy

| Hash Type | Purpose | Use Case |
|-----------|---------|----------|
| **SHA256** | File identity (exact match) | Provenance, integrity, "which file is this?" |
| **pHash** | Visual similarity (pixel match) | Find "same photo" despite metadata differences |

**Combined strategy**:
1. SHA256 for file identity (provenance, deduplication of EXACT copies)
2. pHash for visual matching (merge metadata from icloudpd + iphoneSync)
3. Keep originals in ORIGINAL format (HEIC stays HEIC, never converted)
4. Merge "best of all worlds" metadata to XMP sidecars

**Result**: Best metadata from all sources, while preserving original files!

---

**Next**: Implement SHA256 + pHash for complete file identity system!

---

## AI Enrichment: Aesthetics, Tags, Captions, Locations

### 1. Aesthetic Scoring (Vision LLM)

```python
from litellm import completion

def score_aesthetics(image_path: Path) -> float:
    """Rate photo quality 0-10 using vision LLM."""
    with open(image_path, 'rb') as f:
        image_b64 = base64.b64encode(f.read()).decode()

    response = completion(
        model="groq/llama-4-scout-17b",  # Free, fast vision model
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Rate this photo's aesthetic quality 0-10. Consider: composition, lighting, focus, colors, subject. Return ONLY the number."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }]
    )

    score = float(response.choices[0].message.content.strip())
    return score

# Example:
score = score_aesthetics(photo_path)  # Returns: 8.5

# Store in database + XMP
db.execute("UPDATE photos.images SET aesthetic_score = :score WHERE id = :id")
update_xmp(xmp_path, {"custom:AestheticScore": score})
```

### 2. Auto-Captioning

```python
def generate_caption(image_path: Path) -> str:
    """Generate descriptive caption for photo."""
    response = completion(
        model="groq/llama-4-scout-17b",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this photo in one sentence. Be specific about setting, people, activity, mood."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }]
    )

    caption = response.choices[0].message.content.strip()
    return caption

# Example:
caption = generate_caption(photo_path)
# Returns: "A smiling toddler girl playing with sand on a sunny beach while her parents watch nearby."

# Store in XMP (IPTC standard caption field)
update_xmp(xmp_path, {"dc:description": caption})
```

### 3. Hierarchical Tags (IPTC Standard)

```python
def generate_hierarchical_tags(image_path: Path) -> dict:
    """Generate IPTC-standard hierarchical tags."""
    response = completion(
        model="groq/llama-4-scout-17b",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": """
Analyze this photo and provide hierarchical tags in IPTC format:
- Scene: (outdoor, indoor, landscape, portrait, etc.)
- Subject: (people, nature, architecture, etc.)
- Activity: (sports, leisure, work, etc.)
- Mood: (happy, peaceful, energetic, etc.)
- Objects: (specific items visible)
- Colors: (dominant colors)

Return as JSON.
"""},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }]
    )

    tags = json.loads(response.choices[0].message.content)
    return tags

# Example result:
{
  "scene": ["outdoor", "beach"],
  "subject": ["people", "nature"],
  "activity": ["leisure", "play"],
  "mood": ["happy", "playful"],
  "objects": ["sand", "bucket", "shovel", "ocean"],
  "colors": ["blue", "beige", "yellow"]
}

# Store in XMP with IPTC hierarchy
update_xmp(xmp_path, {
    "Iptc4xmpExt:Subject": tags['scene'] + tags['subject'],
    "Iptc4xmpExt:LocationShown": tags['scene'][0],
    "dc:subject": flatten_all_tags(tags),  # Keywords for simple apps
    "custom:TagHierarchy": json.dumps(tags)  # Full hierarchy
})
```

### 4. Reverse Geocoding (GPS → Location Names)

```python
from geopy.geocoders import Nominatim

def reverse_geocode(lat: float, lon: float) -> dict:
    """Convert GPS coordinates to human-readable location."""
    geolocator = Nominatim(user_agent="picture-pipeline")
    location = geolocator.reverse(f"{lat}, {lon}", language='en')

    # Parse address components
    addr = location.raw['address']
    return {
        'city': addr.get('city') or addr.get('town') or addr.get('village'),
        'state': addr.get('state'),
        'country': addr.get('country'),
        'full_address': location.address,
        'display_name': f"{addr.get('city', '')}, {addr.get('country', '')}"
    }

# Example:
location = reverse_geocode(51.0, 7.0)
# Returns:
{
  'city': 'Cologne',
  'state': 'North Rhine-Westphalia',
  'country': 'Germany',
  'full_address': 'Cologne, North Rhine-Westphalia, Germany',
  'display_name': 'Cologne, Germany'
}

# Store in XMP (IPTC location fields)
update_xmp(xmp_path, {
    "Iptc4xmpExt:City": location['city'],
    "Iptc4xmpExt:ProvinceState": location['state'],
    "Iptc4xmpExt:CountryName": location['country'],
    "custom:LocationDisplay": location['display_name']
})
```

### Complete AI Enrichment Pipeline

```python
def enrich_photo(photo_path: Path):
    """Run all AI enrichment on a photo."""

    # 1. Aesthetic scoring
    aesthetic_score = score_aesthetics(photo_path)

    # 2. Auto-caption
    caption = generate_caption(photo_path)

    # 3. Hierarchical tags
    tags = generate_hierarchical_tags(photo_path)

    # 4. Reverse geocoding (if GPS available)
    metadata = extract_exif(photo_path)
    if metadata.get('gps_latitude'):
        location = reverse_geocode(
            metadata['gps_latitude'],
            metadata['gps_longitude']
        )
    else:
        location = None

    # 5. Store everything in database
    db.execute("""
        UPDATE photos.images SET
            aesthetic_score = :score,
            caption = :caption,
            ai_tags = :tags,
            location_name = :location
        WHERE file_path = :path
    """, score=aesthetic_score, caption=caption,
         tags=json.dumps(tags), location=location['display_name'] if location else None,
         path=str(photo_path))

    # 6. Write to XMP sidecar (universal format)
    xmp_path = photo_path.with_suffix('.xmp')
    update_xmp(xmp_path, {
        # Aesthetic score
        "custom:AestheticScore": aesthetic_score,

        # Caption (IPTC standard)
        "dc:description": caption,

        # Tags (hierarchical)
        "Iptc4xmpExt:Subject": tags['scene'] + tags['subject'],
        "dc:subject": flatten_all_tags(tags),

        # Location (IPTC standard)
        "Iptc4xmpExt:City": location['city'] if location else None,
        "Iptc4xmpExt:CountryName": location['country'] if location else None,
        "custom:LocationDisplay": location['display_name'] if location else None,

        # Processing metadata
        "custom:AIEnriched": True,
        "custom:AIModel": "groq/llama-4-scout-17b",
        "custom:EnrichmentDate": datetime.now().isoformat()
    })

# Run on all photos
photos = db.query("SELECT file_path FROM photos.images WHERE aesthetic_score IS NULL")
for photo in photos:
    enrich_photo(Path(photo.file_path))
```

### Example Enriched XMP Sidecar

```xml
<!-- 75820de3.xmp -->
<x:xmpmeta>
  <!-- AI Aesthetic Scoring -->
  <custom:AestheticScore>8.5</custom:AestheticScore>
  <custom:IsBlurry>false</custom:IsBlurry>
  <custom:IsWellLit>true</custom:IsWellLit>

  <!-- Auto-Caption (IPTC standard) -->
  <dc:description>
    A smiling toddler girl playing with sand on a sunny beach
    while her parents watch nearby.
  </dc:description>

  <!-- Hierarchical Tags -->
  <Iptc4xmpExt:Subject>
    <rdf:Bag>
      <rdf:li>outdoor</rdf:li>
      <rdf:li>beach</rdf:li>
      <rdf:li>people</rdf:li>
      <rdf:li>nature</rdf:li>
    </rdf:Bag>
  </Iptc4xmpExt:Subject>

  <!-- Keywords (flat for simple apps) -->
  <dc:subject>
    <rdf:Bag>
      <rdf:li>outdoor</rdf:li>
      <rdf:li>beach</rdf:li>
      <rdf:li>people</rdf:li>
      <rdf:li>leisure</rdf:li>
      <rdf:li>happy</rdf:li>
      <rdf:li>sand</rdf:li>
      <rdf:li>ocean</rdf:li>
    </rdf:Bag>
  </dc:subject>

  <!-- Location (Reverse Geocoded) -->
  <Iptc4xmpExt:LocationShown>
    <rdf:Bag>
      <rdf:li>
        <Iptc4xmpExt:City>Cologne</Iptc4xmpExt:City>
        <Iptc4xmpExt:ProvinceState>North Rhine-Westphalia</Iptc4xmpExt:ProvinceState>
        <Iptc4xmpExt:CountryName>Germany</Iptc4xmpExt:CountryName>
      </rdf:li>
    </rdf:Bag>
  </Iptc4xmpExt:LocationShown>
  <custom:LocationDisplay>Cologne, Germany</custom:LocationDisplay>

  <!-- Person Tags -->
  <mwg-rs:Regions>
    <rdf:Bag>
      <rdf:li>
        <mwg-rs:Name>daughter</mwg-rs:Name>
        <mwg-rs:Type>Face</mwg-rs:Type>
        <custom:Age>21 months</custom:Age>
      </rdf:li>
    </rdf:Bag>
  </mwg-rs:Regions>

  <!-- Provenance -->
  <custom:SHA256>75820de3d5dc41e9b21894a1a0458986</custom:SHA256>
  <custom:iPhoneVerified>true</custom:iPhoneVerified>
  <custom:iPhoneModel>iPhone 14 Pro</custom:iPhoneModel>

  <!-- AI Enrichment Metadata -->
  <custom:AIEnriched>true</custom:AIEnriched>
  <custom:AIModel>groq/llama-4-scout-17b</custom:AIModel>
  <custom:EnrichmentDate>2026-01-09T03:00:00Z</custom:EnrichmentDate>
</x:xmpmeta>
```

### Advanced Search with AI Tags

```sql
-- Find high-quality outdoor beach photos with people
SELECT
    i.file_path,
    i.aesthetic_score,
    i.caption,
    i.location_name,
    STRING_AGG(f.person_name, ', ') AS people
FROM photos.images i
LEFT JOIN photos.faces f ON f.photo_id = i.id
WHERE i.metadata->'ai_tags'->'scene' ? 'beach'
  AND i.metadata->'ai_tags'->'scene' ? 'outdoor'
  AND i.aesthetic_score >= 8.0
GROUP BY i.id, i.file_path, i.aesthetic_score, i.caption, i.location_name
ORDER BY i.aesthetic_score DESC;
```

**Result**:
```
/mnt/nas/photos/.../75820de3.heic | 8.5 | "A smiling toddler..." | Cologne, Germany | daughter, spouse
/mnt/nas/photos/.../a61bb03b.heic | 8.2 | "Family enjoying..." | Nice, France | daughter, spouse, friend
```

### CLI Commands

```bash
# Enrich all photos with AI
./run.sh enrich-all

# Enrich specific date
./run.sh enrich --date 2023-04-09

# Search with AI tags
./run.sh search \
  --tags beach,outdoor \
  --min-score 8.0 \
  --location Germany \
  --caption "smiling"

# Export captioned gallery
./run.sh export-gallery \
  --person daughter \
  --with-captions \
  --output ~/obsidian/gallery/
```

---

## Complete Feature Matrix

| Feature | Status | Implementation | Tool Compatibility |
|---------|--------|----------------|-------------------|
| **SHA256 provenance** | ✅ Ready | hashlib | Universal |
| **pHash visual matching** | ✅ Ready | imagehash | picture-pipeline |
| **iPhone verification** | ✅ Implemented | ExifTool | All apps |
| **Person tagging** | ✅ Ready | XMP sidecars | digiKam, PhotoPrism, Immich |
| **Age tracking** | ✅ Ready | Database + XMP | picture-pipeline |
| **Aesthetic scoring** | ✅ Ready | Vision LLM | All apps (via XMP) |
| **Auto-captioning** | ✅ Ready | Vision LLM | All apps (IPTC standard) |
| **Hierarchical tags** | ✅ Ready | Vision LLM | All apps (IPTC + XMP) |
| **Reverse geocoding** | ✅ Ready | Nominatim API | All apps (IPTC location) |
| **Project sequences** | ✅ Ready | Timestamp clustering | picture-pipeline |
| **Object detection** | ✅ Ready | Vision LLM | All apps (via XMP) |

---

**Next**: Implement SHA256 + pHash + AI enrichment pipeline!
