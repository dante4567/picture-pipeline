# Provenance & Quick Search: Bang for Buck

**Focus**: SHA256 hashes for provenance + Quick "best photo of X" search.

---

## SHA256 Provenance: Cryptographic Proof

### What is Provenance?

**Provenance** = Cryptographic proof that a file hasn't been altered.

```
Original iPhone photo → SHA256 hash → 75820de3d5dc41e9b21894a1a0458986

IF hash matches → File is IDENTICAL to original (bit-for-bit)
IF hash differs → File has been modified (tampered)
```

**Use cases**:
1. **Legal proof**: "This photo is the original from my iPhone, unaltered"
2. **Deduplication**: Same hash = same photo (even if renamed)
3. **Integrity verification**: Check if files corrupted during transfer
4. **Tamper detection**: Detect if photo was edited/manipulated

---

## Simplified Database Schema

### Focus on what matters: Hash, Person, Quality

```sql
-- Core photo metadata (SIMPLE!)
CREATE TABLE photos.images (
    id SERIAL PRIMARY KEY,

    -- Provenance (CRITICAL!)
    sha256_hash VARCHAR(64) UNIQUE NOT NULL,  -- Cryptographic proof
    file_path TEXT NOT NULL,
    file_size BIGINT,

    -- iPhone verification
    is_iphone_photo BOOLEAN DEFAULT FALSE,
    iphone_model VARCHAR(100),
    gps_latitude FLOAT,
    gps_longitude FLOAT,
    gps_date_time TIMESTAMPTZ,  -- From icloudpd (legal proof!)
    date_taken TIMESTAMPTZ,

    -- Quality scoring (for "best photo" search)
    aesthetic_score FLOAT,  -- 0.0-10.0 (AI-scored beauty)
    is_blurry BOOLEAN,
    is_well_lit BOOLEAN,

    -- Simple metadata
    xmp_path TEXT,
    metadata JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- People registry (with birthdate for age tracking!)
CREATE TABLE photos.people (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,  -- 'daughter', 'spouse', 'friend'
    birthdate DATE,  -- For age calculation
    relationship VARCHAR(50),  -- 'daughter', 'spouse', 'parent', 'friend'
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- People in photos (SIMPLE!)
CREATE TABLE photos.faces (
    id SERIAL PRIMARY KEY,
    photo_id INTEGER REFERENCES photos.images(id),
    person_id INTEGER REFERENCES photos.people(id),

    -- Who is this?
    person_name VARCHAR(255) NOT NULL,  -- Denormalized for speed

    -- Age at time of photo (calculated!)
    age_months INTEGER,  -- For children (daughter: 24 months old)
    age_years INTEGER,   -- For adults (spouse: 35 years old)

    -- How sure are we?
    confidence FLOAT,  -- 0.0-1.0
    verified_by VARCHAR(20),  -- 'user' or 'ai'

    -- Face location (optional, for display)
    region_x FLOAT,
    region_y FLOAT,
    region_w FLOAT,
    region_h FLOAT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Photo sequences / projects (for burst detection and keyword grouping)
CREATE TABLE photos.sequences (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),  -- 'HomeAutomation debugging 2023-04-09'
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    photo_count INTEGER DEFAULT 0,

    -- Project keywords (from RAG system)
    keywords TEXT[],  -- ['homeassistant', 'debugging', 'mqtt']
    project_name VARCHAR(255),  -- Link to RAG project
    rag_context TEXT,  -- Context from RAG about what was happening

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Link photos to sequences
CREATE TABLE photos.sequence_members (
    sequence_id INTEGER REFERENCES photos.sequences(id),
    photo_id INTEGER REFERENCES photos.images(id),
    sequence_order INTEGER,  -- Order within sequence
    PRIMARY KEY (sequence_id, photo_id)
);

CREATE INDEX idx_faces_person ON photos.faces(person_name);
CREATE INDEX idx_faces_photo ON photos.faces(photo_id);
CREATE INDEX idx_images_score ON photos.images(aesthetic_score DESC);
CREATE INDEX idx_images_date ON photos.images(date_taken DESC);
CREATE INDEX idx_sequences_time ON photos.sequences(start_time, end_time);
CREATE INDEX idx_sequences_keywords ON photos.sequences USING GIN(keywords);
```

**That's it!** No complex workflow tracking unless needed.

---

## Quick Search: "Best Photo of Person X"

### Example Queries

#### 1. Best photo of daughter
```sql
SELECT
    i.id,
    i.file_path,
    i.aesthetic_score,
    i.date_taken,
    f.confidence AS face_confidence
FROM photos.images i
JOIN photos.faces f ON f.photo_id = i.id
WHERE f.person_name = 'daughter'
  AND f.verified_by = 'user'  -- Only confirmed faces
  AND i.is_blurry = FALSE
  AND i.is_well_lit = TRUE
ORDER BY i.aesthetic_score DESC
LIMIT 10;
```

**Result**: Top 10 best quality photos of daughter.

#### 2. Best photo of daughter AND spouse together
```sql
WITH daughter_photos AS (
  SELECT photo_id FROM photos.faces WHERE person_name = 'daughter'
),
spouse_photos AS (
  SELECT photo_id FROM photos.faces WHERE person_name = 'spouse'
)
SELECT
    i.id,
    i.file_path,
    i.aesthetic_score,
    i.date_taken
FROM photos.images i
WHERE i.id IN (SELECT photo_id FROM daughter_photos)
  AND i.id IN (SELECT photo_id FROM spouse_photos)
  AND i.is_blurry = FALSE
ORDER BY i.aesthetic_score DESC
LIMIT 10;
```

**Result**: Best photos with BOTH daughter AND spouse.

#### 3. Best recent photos (last month)
```sql
SELECT
    i.file_path,
    i.aesthetic_score,
    i.date_taken,
    STRING_AGG(f.person_name, ', ') AS people
FROM photos.images i
LEFT JOIN photos.faces f ON f.photo_id = i.id
WHERE i.date_taken >= NOW() - INTERVAL '1 month'
  AND i.is_blurry = FALSE
GROUP BY i.id, i.file_path, i.aesthetic_score, i.date_taken
ORDER BY i.aesthetic_score DESC
LIMIT 20;
```

**Result**: Best 20 photos from last month with people listed.

#### 4. Find all photos at a location (GPS)
```sql
-- Photos taken in Germany (rough bounding box)
SELECT
    i.file_path,
    i.gps_latitude,
    i.gps_longitude,
    i.gps_date_time,
    i.aesthetic_score
FROM photos.images i
WHERE i.gps_latitude BETWEEN 47.0 AND 55.0
  AND i.gps_longitude BETWEEN 6.0 AND 15.0
  AND i.is_iphone_photo = TRUE
ORDER BY i.gps_date_time DESC;
```

**Result**: All iPhone photos taken in Germany, chronologically.

#### 5. Photos of daughter at specific age
```sql
-- Find photos when daughter was 18-24 months old
SELECT
    i.file_path,
    i.date_taken,
    f.age_months,
    i.aesthetic_score
FROM photos.images i
JOIN photos.faces f ON f.photo_id = i.id
WHERE f.person_name = 'daughter'
  AND f.age_months BETWEEN 18 AND 24
  AND f.verified_by = 'user'
ORDER BY i.aesthetic_score DESC;
```

**Result**: Best photos of daughter between 18-24 months old.

#### 6. Photos from a project/sequence (screenshots + photos)
```sql
-- Find all photos from HomeAutomation project on 2023-04-09
SELECT
    i.file_path,
    i.date_taken,
    sm.sequence_order,
    s.keywords
FROM photos.images i
JOIN photos.sequence_members sm ON sm.photo_id = i.id
JOIN photos.sequences s ON s.id = sm.sequence_id
WHERE s.project_name = 'HomeAutomation'
  AND DATE(s.start_time) = '2023-04-09'
ORDER BY sm.sequence_order;
```

**Result**: All photos/screenshots from HomeAutomation project on that day, in sequence.

#### 7. Filter by objects/scene (AI tags)
```sql
-- Find photos with "outdoor" and "beach" scene
SELECT
    i.file_path,
    i.aesthetic_score,
    i.metadata->'ai_tags' AS tags
FROM photos.images i
WHERE i.metadata->'ai_tags' ? 'outdoor'
  AND i.metadata->'ai_tags' ? 'beach'
  AND i.aesthetic_score > 7.0
ORDER BY i.aesthetic_score DESC;
```

**Result**: High-quality outdoor beach photos (AI-detected).

---

## XMP Sidecar: Minimal But Universal

### Only store what ALL apps need:

```xml
<!-- 75820de3.xmp -->
<x:xmpmeta>
  <!-- Person tags (universal) -->
  <mwg-rs:Regions>
    <rdf:Bag>
      <rdf:li>
        <mwg-rs:Name>daughter</mwg-rs:Name>
        <mwg-rs:Type>Face</mwg-rs:Type>
        <custom:Confidence>0.98</custom:Confidence>
      </rdf:li>
    </rdf:Bag>
  </mwg-rs:Regions>

  <!-- Keywords (fallback for apps without face support) -->
  <dc:subject>
    <rdf:Bag>
      <rdf:li>daughter</rdf:li>
      <rdf:li>family</rdf:li>
    </rdf:Bag>
  </dc:subject>

  <!-- Provenance (hash for integrity) -->
  <custom:SHA256>75820de3d5dc41e9b21894a1a0458986</custom:SHA256>

  <!-- Quality scores -->
  <custom:AestheticScore>8.5</custom:AestheticScore>
  <custom:IsBlurry>false</custom:IsBlurry>
  <custom:IsWellLit>true</custom:IsWellLit>

  <!-- iPhone verification -->
  <custom:iPhoneVerified>true</custom:iPhoneVerified>
  <custom:iPhoneModel>iPhone 14 Pro</custom:iPhoneModel>
</x:xmpmeta>
```

**That's all you need!** Apps read person tags, picture-pipeline uses hashes for provenance.

---

## Provenance Chain Example

### Original iPhone photo → Import → Verification

```python
# Step 1: Import photo
photo_path = Path("/mnt/nas-photos/icloudpd/.../photo.heic")
sha256 = calculate_hash(photo_path)
# Result: "75820de3d5dc41e9b21894a1a0458986"

# Step 2: Store in database with hash
db.execute("""
    INSERT INTO photos.images (sha256_hash, file_path, ...)
    VALUES (:hash, :path, ...)
""", hash=sha256, path=photo_path)

# Step 3: Write hash to XMP (provenance!)
write_xmp(photo_path.with_suffix('.xmp'), {'SHA256': sha256})

# Step 4: Years later, verify integrity
current_hash = calculate_hash(photo_path)
original_hash = db.query("SELECT sha256_hash FROM photos.images WHERE file_path = :path")

if current_hash == original_hash:
    print("✓ Photo is ORIGINAL, unaltered")
else:
    print("✗ Photo has been MODIFIED! Possible tampering!")
```

### Legal Use Case

**Scenario**: Need to prove you were at a location on a specific date.

**Evidence**:
1. Original iPhone photo (unaltered, hash-verified)
2. GPS coordinates: 51.0, 7.0
3. GPS timestamp: 2023-04-09 11:53:25+02
4. iPhone model: iPhone 14 Pro
5. SHA256 hash: 75820de3d5dc41e9b21894a1a0458986

**Verification**:
```sql
SELECT
    file_path,
    sha256_hash,
    gps_latitude,
    gps_longitude,
    gps_date_time,
    iphone_model,
    is_iphone_photo
FROM photos.images
WHERE sha256_hash = '75820de3d5dc41e9b21894a1a0458986';
```

**Proof**: "This photo (hash-verified as original) shows I was at 51.0°N 7.0°E at 11:53:25 on April 9, 2023, as recorded by my iPhone 14 Pro's GPS."

---

## Simplified Import Pipeline

### Focus on: Hash → Verify → Tag

```bash
# Import photos (calculate hashes, verify iPhone)
./run.sh import --source icloudpd

# Detect faces (AI auto-detection)
./run.sh detect-faces

# User confirms people in ANY app (digiKam, PhotoPrism, etc.)
# → Syncs automatically via XMP sidecars

# Score photos for quality
./run.sh score-quality

# Search for best photos
./run.sh search --person daughter --limit 10
```

**Result**: Best 10 photos of daughter, ranked by quality.

---

## CLI Commands for Quick Search

### Fast queries from command line:

```bash
# Best photo of daughter
./run.sh best-photo daughter

# Best photo of daughter and spouse together
./run.sh best-photo daughter spouse

# Best recent photos (last 30 days)
./run.sh best-recent --days 30

# Find photos by location (Germany)
./run.sh find-location --lat 51.0 --lon 7.0 --radius 100km

# Verify photo hasn't been tampered
./run.sh verify-hash /path/to/photo.heic
```

**Output**:
```
✓ Best photo of daughter:
  /mnt/nas/photos/originals/2023/2023-04/pictures/75820de3.heic
  Score: 9.2/10
  Date: 2023-04-09 11:53:25
  People: daughter, spouse
  Hash: 75820de3d5dc41e9b21894a1a0458986 (verified ✓)
```

---

## Obsidian Integration: "Best of" Gallery

### Auto-generated markdown notes:

```bash
# Generate "Best Photos" gallery for Obsidian
./run.sh export-gallery --person daughter --output ~/obsidian/vault/
```

**Result**: `Best Photos - daughter.md`
```markdown
# Best Photos - daughter

Generated: 2026-01-09

## Top 10 All-Time

![](mnt/nas/photos/originals/2023/2023-04/pictures/75820de3.heic)
**Score**: 9.2/10 | **Date**: 2023-04-09 | **People**: daughter, spouse
**Location**: Germany (51.0, 7.0) | **Hash**: 75820de3...

![](mnt/nas/photos/originals/2023/2023-06/pictures/a61bb03b.heic)
**Score**: 8.9/10 | **Date**: 2023-06-15 | **People**: daughter
**Location**: Park (51.2, 6.8) | **Hash**: a61bb03b...

... (8 more) ...

## Recent (Last 30 Days)

![](...)
...

## By Location

### Germany
- 234 photos
- Best: 75820de3.heic (9.2/10)

### France
- 89 photos
- Best: c7f9e2a1.heic (8.7/10)
```

---

## Summary: Bang for Buck

### ✅ SHA256 Provenance (SIMPLE!)
- Hash every photo on import
- Store in database + XMP sidecar
- Verify integrity anytime
- Legal proof of originality

### ✅ Quick "Best Photo" Search (POWERFUL!)
- Person name → Best photos
- Multiple people → Photos together
- Date range → Recent best
- Location → GPS-based search
- Quality scores → Auto-ranked

### ✅ Universal Person Tags (COMPATIBLE!)
- Tag in ANY app (digiKam, PhotoPrism, Immich)
- Syncs via XMP sidecars
- All apps see same tags
- No vendor lock-in

### ❌ Skip Over-Engineering
- No complex workflow tracking (unless needed later)
- No deep audit logs (just basics)
- No version control (XMP is enough)
- Focus on SEARCH and PROVENANCE

---

## Implementation Priority

1. **SHA256 hashing** (provenance foundation)
2. **Person tagging** (via XMP)
3. **Quality scoring** (aesthetic AI)
4. **Quick search** (SQL queries)
5. **CLI commands** (./run.sh best-photo)

**Result**: Find "best photo of daughter" in <1 second!

---

## Age Tracking Implementation

### Automatic age calculation:

```python
from datetime import date

# Setup: Register people with birthdates
db.execute("""
    INSERT INTO photos.people (name, birthdate, relationship)
    VALUES
        ('daughter', '2021-06-15', 'daughter'),
        ('spouse', '1988-03-20', 'spouse'),
        ('self', '1985-11-10', 'self');
""")

# When confirming person in photo, calculate age
def calculate_age(birthdate: date, photo_date: date) -> tuple[int, int]:
    """Return (age_years, age_months)"""
    years = photo_date.year - birthdate.year
    months = (photo_date.year - birthdate.year) * 12 + (photo_date.month - birthdate.month)

    # Adjust if birthday hasn't occurred yet this year
    if photo_date.month < birthdate.month or \
       (photo_date.month == birthdate.month and photo_date.day < birthdate.day):
        years -= 1
        months -= 1

    return (years, months)

# Example: Photo taken 2023-04-09, daughter born 2021-06-15
birthdate = date(2021, 6, 15)
photo_date = date(2023, 4, 9)
age_years, age_months = calculate_age(birthdate, photo_date)
# Result: age_years=1, age_months=21

# Store in database
db.execute("""
    UPDATE photos.faces
    SET age_years = :years, age_months = :months
    WHERE person_name = 'daughter' AND photo_id = :photo_id
""", years=age_years, months=age_months, photo_id=photo_id)
```

### Query examples:

```sql
-- Photos of daughter as a baby (0-12 months)
SELECT * FROM photos.images i
JOIN photos.faces f ON f.photo_id = i.id
WHERE f.person_name = 'daughter' AND f.age_months <= 12;

-- Photos of daughter as a toddler (12-36 months)
WHERE f.age_months BETWEEN 12 AND 36;

-- Photos of spouse at age 35
WHERE f.person_name = 'spouse' AND f.age_years = 35;
```

---

## Sequence Detection Implementation

### Auto-detect photo bursts and project sequences:

```python
from datetime import timedelta

def detect_sequences(photos: list, gap_threshold: timedelta = timedelta(minutes=5)):
    """Group photos taken within gap_threshold into sequences."""
    sequences = []
    current_sequence = []

    sorted_photos = sorted(photos, key=lambda p: p.date_taken)

    for i, photo in enumerate(sorted_photos):
        if i == 0:
            current_sequence = [photo]
            continue

        time_gap = photo.date_taken - sorted_photos[i-1].date_taken

        if time_gap <= gap_threshold:
            # Same sequence
            current_sequence.append(photo)
        else:
            # New sequence
            if len(current_sequence) >= 3:  # Only sequences with 3+ photos
                sequences.append(current_sequence)
            current_sequence = [photo]

    # Add final sequence
    if len(current_sequence) >= 3:
        sequences.append(current_sequence)

    return sequences

# Example usage:
photos = db.query("SELECT * FROM photos.images WHERE date_taken::date = '2023-04-09'")
sequences = detect_sequences(photos, gap_threshold=timedelta(minutes=5))

# Create sequence record
for seq in sequences:
    start_time = seq[0].date_taken
    end_time = seq[-1].date_taken

    # Try to infer project from screenshots (OCR text extraction)
    keywords = extract_keywords_from_screenshots(seq)

    # Link to RAG system (e.g., HomeAutomation project was active at this time)
    project = find_active_project(start_time, keywords)

    # Store sequence
    seq_id = db.execute("""
        INSERT INTO photos.sequences (name, start_time, end_time, photo_count, keywords, project_name)
        VALUES (:name, :start, :end, :count, :keywords, :project)
        RETURNING id
    """, name=f"Sequence {start_time.strftime('%Y-%m-%d %H:%M')}",
         start=start_time, end=end_time, count=len(seq),
         keywords=keywords, project=project.name if project else None)

    # Link photos to sequence
    for i, photo in enumerate(seq):
        db.execute("""
            INSERT INTO photos.sequence_members (sequence_id, photo_id, sequence_order)
            VALUES (:seq, :photo, :order)
        """, seq=seq_id, photo=photo.id, order=i)
```

### Link to RAG projects:

```python
def find_active_project(timestamp: datetime, keywords: list[str]):
    """Find which RAG project was active at this time."""
    # Query life-log for active projects at this time
    project = db.execute("""
        SELECT project_name, keywords
        FROM lifelog.events
        WHERE event_type = 'project_work'
          AND :timestamp BETWEEN start_time AND end_time
        LIMIT 1
    """, timestamp=timestamp)

    if project:
        return project

    # Fallback: Match keywords with known projects
    for known_project in get_all_projects():
        if any(kw in known_project.keywords for kw in keywords):
            return known_project

    return None
```

---

## Object/Scene Detection with PhotoPrism Integration

### Use existing AI from PhotoPrism:

```python
# PhotoPrism already does object/scene detection
# Read its database to populate picture-pipeline

def import_photoprism_tags():
    """Import AI tags from PhotoPrism database."""
    photoprism_db = connect_to_photoprism_db()

    # Get all photos with AI tags
    results = photoprism_db.execute("""
        SELECT
            p.photo_path,
            GROUP_CONCAT(l.label_name) AS tags
        FROM photos p
        JOIN photos_labels pl ON pl.photo_id = p.id
        JOIN labels l ON l.id = pl.label_id
        WHERE l.label_source = 'image'  -- AI-detected
        GROUP BY p.photo_path
    """)

    # Update picture-pipeline database
    for row in results:
        photo = db.query("SELECT id FROM photos.images WHERE file_path = :path", path=row.photo_path)
        if photo:
            db.execute("""
                UPDATE photos.images
                SET metadata = metadata || jsonb_build_object('ai_tags', :tags)
                WHERE id = :id
            """, tags=row.tags.split(','), id=photo.id)
```

### Or use vision LLM (Groq llama-4-scout-17b):

```python
from litellm import completion

def detect_objects_and_scene(image_path: Path) -> dict:
    """Use vision LLM to detect objects and scene."""
    with open(image_path, 'rb') as f:
        image_b64 = base64.b64encode(f.read()).decode()

    response = completion(
        model="groq/llama-4-scout-17b",  # Groq vision model
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "List all objects, people, and scene type in this photo. Format: objects: [...], scene: [...]"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }]
    )

    # Parse response
    tags = parse_llm_tags(response.choices[0].message.content)
    return tags

# Example result:
# {
#   "objects": ["beach", "umbrella", "ocean", "sand"],
#   "scene": "outdoor",
#   "people_count": 2
# }
```

---

## CLI Commands (Extended)

```bash
# Age-based search
./run.sh search --person daughter --age-months 18-24 --limit 10

# Project/sequence search
./run.sh search --project HomeAutomation --date 2023-04-09

# Object/scene search
./run.sh search --tags outdoor,beach --min-score 7.0

# Combined search
./run.sh search --person daughter --tags beach --age-months 12-24 --limit 5
# Result: Best beach photos of daughter when she was 12-24 months old
```

---

## Storage Update (Complete Inventory)

| Source | Photos | Storage | Key Metadata |
|--------|--------|---------|--------------|
| **icloudpd** | 51,187 | **83 GB** | ✅ GPS Date/Time (CRITICAL!) |
| **iphoneSync** | 61,323 | **90 GB** | ✅ HDR/AF, +10,136 more photos |
| **myPicturesFromMyIphone** | 23,543 | ~40 GB* | ⏳ Analyzing... |
| **TOTAL** | 136,053 | ~213 GB | |

*Estimated, final count pending

**Savings after deduplication**: ~40-50% (~85-100 GB)

---

*Next: Implement SHA256 hashing and deduplication*
