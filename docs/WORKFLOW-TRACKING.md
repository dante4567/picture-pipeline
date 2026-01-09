# Workflow Tracking & Universal Person Tagging

**CRITICAL**: Originals NEVER modified. All changes tracked in XMP sidecars + database.

---

## Philosophy: Single Source of Truth for Person Tags

```
┌─────────────────────────────────────────────────────────┐
│ User tags person in ANY app (digiKam, PhotoPrism, etc) │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ picture-pipeline watches XMP sidecars for changes       │
│ Detects: Person added/removed/confirmed/rejected        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Update database (photos.faces, photos.people)          │
│ Propagate to OTHER XMP sidecars (if photo has faces)   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ ALL apps see updated person tags                        │
│ digiKam, PhotoPrism, Immich, etc. re-scan XMP          │
└─────────────────────────────────────────────────────────┘
```

---

## XMP Sidecar: Universal Person Tags

### Example: User confirms "daughter" on a photo

**Workflow**:
1. User opens digiKam, tags face as "daughter"
2. digiKam writes to XMP sidecar: `75820de3.xmp`
3. picture-pipeline detects XMP change (file watcher)
4. Updates database: `photos.faces` table
5. If same person in other photos → update their XMP too
6. PhotoPrism, Immich re-scan and see "daughter" tag

**XMP sidecar format**:
```xml
<!-- 75820de3.xmp -->
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">

    <!-- Person/Face Tags (Universal across all apps) -->
    <rdf:Description rdf:about="">
      <mwg-rs:Regions>
        <rdf:Bag>
          <rdf:li>
            <rdf:Description>
              <!-- Face region coordinates -->
              <mwg-rs:Area>
                <rdf:Description>
                  <stArea:x>0.5</stArea:x>
                  <stArea:y>0.3</stArea:y>
                  <stArea:w>0.2</stArea:w>
                  <stArea:h>0.2</stArea:h>
                </rdf:Description>
              </mwg-rs:Area>

              <!-- Person identification -->
              <mwg-rs:Name>daughter</mwg-rs:Name>
              <mwg-rs:Type>Face</mwg-rs:Type>

              <!-- picture-pipeline enrichment -->
              <custom:PersonUUID>a3f5c7b2-1234-5678-abcd-ef0123456789</custom:PersonUUID>
              <custom:Confidence>0.98</custom:Confidence>
              <custom:VerificationStatus>confirmed</custom:VerificationStatus>
              <custom:VerifiedBy>user</custom:VerifiedBy>
              <custom:VerifiedAt>2026-01-09T02:45:00Z</custom:VerifiedAt>
              <custom:VerifiedApp>digiKam</custom:VerifiedApp>
            </rdf:Description>
          </rdf:li>
        </rdf:Bag>
      </mwg-rs:Regions>

      <!-- Keywords/Tags (for apps that don't support face regions) -->
      <dc:subject>
        <rdf:Bag>
          <rdf:li>daughter</rdf:li>
          <rdf:li>family</rdf:li>
        </rdf:Bag>
      </dc:subject>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
```

**Why this format**:
- ✅ `mwg-rs:Regions` = **Metadata Working Group standard** (digiKam, Lightroom, Picasa)
- ✅ Face coordinates = Works with PhotoPrism, Immich face detection
- ✅ `dc:subject` keywords = Fallback for apps without face region support
- ✅ `custom:*` fields = picture-pipeline enrichment (confidence, verification)

---

## Database Schema: Person Tracking

### photos.people (Person registry)

```sql
CREATE TABLE photos.people (
    id SERIAL PRIMARY KEY,

    -- Person identification
    person_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,

    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMPTZ,
    verified_by VARCHAR(50),  -- 'user' or 'model'

    -- Training data
    face_encoding VECTOR(128),  -- pgvector for face matching
    training_photos INTEGER[] DEFAULT '{}',  -- Array of photo IDs

    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Example:
INSERT INTO photos.people (name, is_verified, verified_by)
VALUES ('daughter', TRUE, 'user');
```

### photos.faces (Face instances per photo)

```sql
CREATE TABLE photos.faces (
    id SERIAL PRIMARY KEY,

    -- Photo reference
    photo_id INTEGER NOT NULL REFERENCES photos.images(id) ON DELETE CASCADE,

    -- Person identification
    person_id INTEGER REFERENCES photos.people(id) ON DELETE SET NULL,
    person_uuid UUID,  -- Matches photos.people.person_uuid
    person_name VARCHAR(255),  -- Denormalized for speed

    -- Face region (bounding box)
    region_x FLOAT NOT NULL,  -- 0.0-1.0 (normalized)
    region_y FLOAT NOT NULL,
    region_w FLOAT NOT NULL,
    region_h FLOAT NOT NULL,

    -- Verification status
    status VARCHAR(20) NOT NULL DEFAULT 'detected',
        -- 'detected', 'confirmed', 'rejected', 'unknown'
    confidence FLOAT,  -- 0.0-1.0

    -- Source tracking
    detected_by VARCHAR(50),  -- 'picture-pipeline', 'digiKam', 'PhotoPrism', 'user'
    verified_by VARCHAR(50),  -- 'user', 'model'
    verified_at TIMESTAMPTZ,
    verified_app VARCHAR(50),  -- App used for verification

    -- Face encoding for matching
    face_encoding VECTOR(128),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(photo_id, region_x, region_y, region_w, region_h)
);

CREATE INDEX idx_faces_person ON photos.faces(person_id);
CREATE INDEX idx_faces_photo ON photos.faces(photo_id);
CREATE INDEX idx_faces_status ON photos.faces(status);
```

---

## Workflow Tracking Per Photo

### photos.processing_log (Audit trail)

```sql
CREATE TABLE photos.processing_log (
    id SERIAL PRIMARY KEY,
    photo_id INTEGER NOT NULL REFERENCES photos.images(id) ON DELETE CASCADE,

    -- Processing step
    step VARCHAR(50) NOT NULL,
        -- 'import', 'hash', 'iphone_verify', 'face_detect', 'face_confirm', etc.
    status VARCHAR(20) NOT NULL,
        -- 'pending', 'processing', 'completed', 'failed'

    -- Details
    details JSONB,  -- Step-specific data
    error_message TEXT,

    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,  -- Milliseconds

    -- Source tracking
    triggered_by VARCHAR(50),  -- 'import', 'user', 'watcher', 'cron'
    processed_by VARCHAR(50),  -- 'picture-pipeline', 'digiKam', etc.

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_processing_log_photo ON photos.processing_log(photo_id);
CREATE INDEX idx_processing_log_step ON photos.processing_log(step);
```

### Example log entries for a single photo:

```sql
-- Step 1: Import from icloudpd
INSERT INTO photos.processing_log (photo_id, step, status, details, duration_ms)
VALUES (1, 'import', 'completed',
  '{"source": "icloudpd", "path": "/mnt/nas-photos/...", "sha256": "75820de3..."}',
  1234);

-- Step 2: Calculate SHA256 hash
INSERT INTO photos.processing_log (photo_id, step, status, details, duration_ms)
VALUES (1, 'hash', 'completed',
  '{"sha256": "75820de3d5dc41e9b21894a1a0458986", "algorithm": "SHA256"}',
  89);

-- Step 3: iPhone verification
INSERT INTO photos.processing_log (photo_id, step, status, details, duration_ms)
VALUES (1, 'iphone_verify', 'completed',
  '{"is_iphone": true, "confidence": 0.8, "model": "iPhone 14 Pro", "ios": "16.4.1"}',
  156);

-- Step 4: Face detection
INSERT INTO photos.processing_log (photo_id, step, status, details, duration_ms)
VALUES (1, 'face_detect', 'completed',
  '{"faces_found": 2, "model": "hog", "confidence": [0.95, 0.87]}',
  423);

-- Step 5: User confirms person
INSERT INTO photos.processing_log (photo_id, step, status, details, triggered_by, processed_by)
VALUES (1, 'face_confirm', 'completed',
  '{"person": "daughter", "face_region": [0.5, 0.3, 0.2, 0.2], "confidence": 0.98}',
  'user', 'digiKam');

-- Step 6: XMP sidecar updated
INSERT INTO photos.processing_log (photo_id, step, status, details, duration_ms)
VALUES (1, 'xmp_write', 'completed',
  '{"xmp_path": "/mnt/nas/photos/.../75820de3.xmp", "fields_updated": ["mwg-rs:Regions", "dc:subject"]}',
  67);

-- Step 7: Metadata merge from iphoneSync
INSERT INTO photos.processing_log (photo_id, step, status, details, duration_ms)
VALUES (1, 'metadata_merge', 'completed',
  '{"source": "iphoneSync", "merged_fields": ["HDRHeadroom", "HDRGain", "AFConfidence"]}',
  45);
```

---

## XMP Sidecar: Complete Workflow Tracking

**In addition to person tags, XMP tracks ALL processing steps**:

```xml
<!-- 75820de3.xmp -->
<x:xmpmeta>
  <!-- ... Person tags above ... -->

  <!-- picture-pipeline workflow tracking -->
  <custom:ProcessingHistory>
    <rdf:Seq>
      <rdf:li>
        <rdf:Description>
          <custom:Step>import</custom:Step>
          <custom:Source>icloudpd</custom:Source>
          <custom:Timestamp>2026-01-09T02:30:00Z</custom:Timestamp>
          <custom:Status>completed</custom:Status>
        </rdf:Description>
      </rdf:li>
      <rdf:li>
        <rdf:Description>
          <custom:Step>hash</custom:Step>
          <custom:Algorithm>SHA256</custom:Algorithm>
          <custom:Hash>75820de3d5dc41e9b21894a1a0458986</custom:Hash>
          <custom:Timestamp>2026-01-09T02:30:01Z</custom:Timestamp>
          <custom:Status>completed</custom:Status>
        </rdf:Description>
      </rdf:li>
      <rdf:li>
        <rdf:Description>
          <custom:Step>iphone_verify</custom:Step>
          <custom:Verified>true</custom:Verified>
          <custom:Confidence>0.8</custom:Confidence>
          <custom:Model>iPhone 14 Pro</custom:Model>
          <custom:Timestamp>2026-01-09T02:30:02Z</custom:Timestamp>
          <custom:Status>completed</custom:Status>
        </rdf:Description>
      </rdf:li>
      <rdf:li>
        <rdf:Description>
          <custom:Step>face_detect</custom:Step>
          <custom:FacesFound>2</custom:FacesFound>
          <custom:Timestamp>2026-01-09T02:30:03Z</custom:Timestamp>
          <custom:Status>completed</custom:Status>
        </rdf:Description>
      </rdf:li>
      <rdf:li>
        <rdf:Description>
          <custom:Step>face_confirm</custom:Step>
          <custom:Person>daughter</custom:Person>
          <custom:VerifiedBy>user</custom:VerifiedBy>
          <custom:VerifiedApp>digiKam</custom:VerifiedApp>
          <custom:Timestamp>2026-01-09T02:45:00Z</custom:Timestamp>
          <custom:Status>completed</custom:Status>
        </rdf:Description>
      </rdf:li>
      <rdf:li>
        <rdf:Description>
          <custom:Step>metadata_merge</custom:Step>
          <custom:Source>iphoneSync</custom:Source>
          <custom:MergedFields>HDRHeadroom,HDRGain,AFConfidence</custom:MergedFields>
          <custom:Timestamp>2026-01-09T02:30:05Z</custom:Timestamp>
          <custom:Status>completed</custom:Status>
        </rdf:Description>
      </rdf:li>
    </rdf:Seq>
  </custom:ProcessingHistory>

  <!-- Current processing status -->
  <custom:LastProcessed>2026-01-09T02:45:00Z</custom:LastProcessed>
  <custom:ProcessingComplete>true</custom:ProcessingComplete>
  <custom:Version>1.0.0</custom:Version>
</x:xmpmeta>
```

---

## Universal Person Tagging Workflow

### Scenario 1: User tags person in digiKam

```python
# 1. User opens digiKam, tags face as "daughter"
# digiKam writes to XMP: 75820de3.xmp

# 2. picture-pipeline file watcher detects change
def on_xmp_modified(xmp_path: Path):
    # Parse XMP sidecar
    xmp_data = parse_xmp(xmp_path)

    # Extract person tags
    for region in xmp_data.get('mwg-rs:Regions', []):
        person_name = region.get('mwg-rs:Name')

        # Check if person exists in database
        person = db.query(Person).filter_by(name=person_name).first()
        if not person:
            # Create new person
            person = Person(name=person_name, verified_by='user')
            db.add(person)

        # Update or create face record
        face = Face(
            photo_id=photo.id,
            person_id=person.id,
            region_x=region['x'],
            region_y=region['y'],
            region_w=region['w'],
            region_h=region['h'],
            status='confirmed',
            verified_by='user',
            verified_app='digiKam',
            verified_at=datetime.now()
        )
        db.add(face)

    db.commit()

    # Log processing step
    log_processing_step(
        photo_id=photo.id,
        step='face_confirm',
        details={'person': person_name, 'app': 'digiKam'}
    )
```

### Scenario 2: User confirms face in PhotoPrism

```python
# 1. User confirms face in PhotoPrism web UI
# PhotoPrism may not write to XMP directly

# 2. picture-pipeline API endpoint receives confirmation
@app.post("/api/faces/confirm")
def confirm_face(photo_id: int, person_name: str, region: dict):
    # Update database
    person = get_or_create_person(person_name)
    face = Face(
        photo_id=photo_id,
        person_id=person.id,
        region_x=region['x'],
        region_y=region['y'],
        region_w=region['w'],
        region_h=region['h'],
        status='confirmed',
        verified_by='user',
        verified_app='PhotoPrism'
    )
    db.add(face)
    db.commit()

    # Write to XMP sidecar (propagate to all apps!)
    photo = get_photo(photo_id)
    xmp_path = photo.xmp_path
    update_xmp_sidecar(xmp_path, {
        'person': person_name,
        'region': region,
        'verified_by': 'user',
        'verified_app': 'PhotoPrism'
    })

    # Log step
    log_processing_step(photo_id, 'face_confirm', {'person': person_name})

    return {"status": "confirmed"}
```

### Scenario 3: User rejects incorrect person tag

```python
# 1. picture-pipeline auto-detected "spouse" but it's actually "friend"
# User rejects in Immich

# 2. Update database
face = db.query(Face).filter_by(photo_id=photo_id, person_name='spouse').first()
face.status = 'rejected'
face.verified_by = 'user'
face.verified_app = 'Immich'
db.commit()

# 3. Update XMP sidecar (remove incorrect tag)
remove_person_from_xmp(xmp_path, person_name='spouse')

# 4. Log rejection
log_processing_step(photo_id, 'face_reject', {'person': 'spouse', 'reason': 'incorrect'})
```

---

## Bi-Directional Sync

### XMP → Database (File watcher)

```python
# Watch for XMP changes from digiKam, Lightroom, etc.
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class XMPWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.xmp'):
            sync_xmp_to_database(Path(event.src_path))

observer = Observer()
observer.schedule(XMPWatcher(), '/mnt/nas/photos/originals/', recursive=True)
observer.start()
```

### Database → XMP (Trigger on insert/update)

```python
# PostgreSQL trigger: When face is confirmed, update XMP
CREATE OR REPLACE FUNCTION update_xmp_on_face_confirm()
RETURNS TRIGGER AS $$
BEGIN
    -- Call picture-pipeline to update XMP sidecar
    PERFORM pg_notify('xmp_update', json_build_object(
        'photo_id', NEW.photo_id,
        'person_name', NEW.person_name,
        'region', json_build_object(
            'x', NEW.region_x,
            'y', NEW.region_y,
            'w', NEW.region_w,
            'h', NEW.region_h
        )
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_xmp_update
AFTER INSERT OR UPDATE ON photos.faces
FOR EACH ROW EXECUTE FUNCTION update_xmp_on_face_confirm();
```

---

## Tool Compatibility Matrix

| App | XMP Read | XMP Write | Person Tags | Face Regions | picture-pipeline Integration |
|-----|----------|-----------|-------------|--------------|------------------------------|
| **digiKam** | ✅ Full | ✅ Full | ✅ Yes | ✅ Yes | ✅ Bi-directional sync |
| **PhotoPrism** | ✅ Full | ⚠️ Partial | ✅ Yes | ✅ Yes | ✅ API + XMP read |
| **Immich** | ⚠️ Basic | ❌ No | ✅ Yes (DB) | ✅ Yes | ✅ API integration |
| **Lightroom** | ✅ Full | ✅ Full | ✅ Yes | ✅ Yes | ✅ XMP sync |
| **Darktable** | ✅ Full | ✅ Full | ⚠️ Limited | ⚠️ Limited | ⚠️ XMP read only |

**Strategy**:
- digiKam, Lightroom: Full bi-directional XMP sync
- PhotoPrism: Read XMP, write via picture-pipeline API
- Immich: Use picture-pipeline API for person tagging
- All tools see same person tags via XMP sidecars

---

## Example: Complete User Workflow

### Day 1: Import photos
```bash
./run.sh import --source icloudpd
# Result: 51,187 photos imported, XMP sidecars created
```

### Day 2: Auto face detection
```bash
./run.sh detect-faces
# Result: Faces detected, stored in database + XMP
# Status: 'detected' (not yet confirmed)
```

### Day 3: User confirms faces in digiKam
- Opens digiKam on desktop
- Reviews detected faces
- Confirms: "This is daughter"
- Rejects: "This is NOT spouse"
- digiKam writes to XMP → picture-pipeline syncs to DB

### Day 4: User adds tag in PhotoPrism
- Opens PhotoPrism on phone
- Sees already-confirmed "daughter" from digiKam ✅
- Adds new person: "friend"
- PhotoPrism → picture-pipeline API → XMP updated → digiKam sees it ✅

### Day 5: Check in Immich
- Opens Immich on tablet
- Sees "daughter" and "friend" tags ✅
- All apps in sync!

---

## Summary

### ✅ Universal Person Tagging

1. **Tag person in ANY app** → Visible in ALL apps
2. **XMP sidecars** = Universal metadata format
3. **Database** = Fast queries, training data
4. **Bi-directional sync** = XMP ↔ Database

### ✅ Workflow Tracking

1. **Every processing step logged** (import, hash, verify, detect, confirm)
2. **Stored in database** (`photos.processing_log` table)
3. **Stored in XMP sidecar** (`custom:ProcessingHistory`)
4. **Audit trail** for debugging and verification

### ✅ Originals Protected

1. **Never modified** (chmod 444, read-only)
2. **All changes in XMP sidecars**
3. **Reversible** (delete XMP = back to original)

---

*Next: Implement person tagging system with XMP sync*
