# Life-Log Integration: Reverse-Engineered Diary

Picture-pipeline as the **authoritative source** for diary reconstruction.

---

## Core Concept: iPhone Photos = Diary Proof

**Verified iPhone photos** provide definitive proof of:
- **WHERE** you were (GPS coordinates)
- **WHEN** you were there (timestamp with timezone)
- **WHO** you were with (face recognition)
- **WHAT** you were doing (scene description)

This is **more reliable** than:
- ❌ Manual diary entries (forgotten, biased)
- ❌ Calendar events (planned, not actual)
- ❌ GPS tracks only (no context)

**iPhone photos** = **Ground truth** for life reconstruction

---

## Data Export to life-log

### Event Schema

```sql
-- life-log database
CREATE SCHEMA lifelog;

CREATE TABLE lifelog.events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,  -- 'photo', 'location', 'activity'

    -- Time
    timestamp TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER,

    -- Location
    location_lat FLOAT,
    location_lon FLOAT,
    location_name TEXT,
    location_accuracy FLOAT,

    -- People
    people TEXT[],  -- ['Daughter', 'Spouse']

    -- Activity
    activity_type VARCHAR(100),  -- 'family_outing', 'meal', 'sports', etc.
    activity_description TEXT,

    -- Source proof
    source_type VARCHAR(50) NOT NULL,  -- 'iphone_photo', 'calendar', 'gps_track'
    source_confidence FLOAT,  -- 0.0-1.0
    source_refs TEXT[],  -- ['photo:sha256', 'photo:sha256']

    -- Metadata
    metadata JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Export Logic

```python
def export_to_lifelog(photo: Photo):
    """Export verified photo as life-log event."""

    # Only export iPhone photos (high confidence)
    if not photo.is_iphone_photo:
        return

    # Only export photos with location
    if not (photo.gps_latitude and photo.gps_longitude):
        return

    # Determine activity type from scene description + people
    activity_type = infer_activity_type(
        scene_description=photo.scene_description,
        people=photo.faces,
        aesthetic_score=photo.aesthetic_score
    )

    event = {
        'event_type': 'photo',
        'timestamp': photo.date_taken,
        'duration_minutes': 5,  # Approximate photo session duration

        'location_lat': photo.gps_latitude,
        'location_lon': photo.gps_longitude,
        'location_name': photo.location_name,
        'location_accuracy': 10.0,  # iPhone GPS accuracy

        'people': [face.person_name for face in photo.faces if face.confidence > 0.95],

        'activity_type': activity_type,
        'activity_description': generate_activity_description(photo),

        'source_type': 'iphone_photo',
        'source_confidence': 1.0,  # iPhone photos = definitive proof
        'source_refs': [f"photo:{photo.sha256}"],

        'metadata': {
            'camera_model': photo.iphone_model,
            'aesthetic_score': photo.aesthetic_score,
            'faces_count': len(photo.faces),
            'scene_description': photo.scene_description
        }
    }

    # Insert into life-log
    db_lifelog.execute(
        "INSERT INTO lifelog.events (...) VALUES (...)",
        event
    )
```

---

## Activity Inference

### Automatic Activity Classification

```python
def infer_activity_type(
    scene_description: str,
    people: List[Face],
    aesthetic_score: float
) -> str:
    """Infer activity type from photo context."""

    # Use LLM for classification
    prompt = f"""
    Given a photo with:
    - Scene: {scene_description}
    - People: {', '.join(p.person_name for p in people)}
    - Aesthetic score: {aesthetic_score}/10

    Classify the activity type from:
    - family_outing
    - meal (breakfast/lunch/dinner)
    - sports/exercise
    - work/meeting
    - travel
    - celebration/event
    - daily_routine
    - hobby/recreation

    Return only the activity type.
    """

    response = litellm.completion(
        model="openai/chat",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()
```

### Example Inferences

| Scene Description | People | Activity Type |
|-------------------|--------|---------------|
| "Young girl playing in park with autumn leaves" | Daughter | family_outing |
| "Family gathered around dinner table with candles" | Daughter, Spouse | meal |
| "Person running on trail in forest" | None | sports/exercise |
| "People sitting at conference table with laptops" | Colleagues | work/meeting |
| "Beach scene with sunset, person in foreground" | Spouse | travel |
| "Birthday cake with lit candles" | Daughter, Family | celebration/event |

---

## Reverse-Engineered Diary Queries

### Example 1: What did I do on 2024-06-15?

```sql
SELECT
  timestamp::time as time,
  activity_type,
  activity_description,
  location_name,
  people,
  source_refs
FROM lifelog.events
WHERE source_type = 'iphone_photo'
  AND DATE(timestamp) = '2024-06-15'
ORDER BY timestamp;
```

**Output**:
```
time     | activity_type  | activity_description              | location    | people           | source_refs
---------|----------------|-----------------------------------|-------------|------------------|-------------
08:30:00 | meal           | Breakfast at home kitchen         | Home        | [Daughter]       | [photo:abc123]
10:15:00 | family_outing  | Park visit, daughter on swings    | City Park   | [Daughter]       | [photo:def456, photo:ghi789]
12:45:00 | meal           | Lunch at cafe outdoor seating     | Downtown    | [Daughter, Spouse] | [photo:jkl012]
15:30:00 | travel         | Driving, highway scene            | Highway 99  | []               | [photo:mno345]
17:00:00 | family_outing  | Beach visit, sunset               | Alki Beach  | [Daughter, Spouse] | [photo:pqr678]
```

### Example 2: Where was my daughter on 2024-06-15?

```sql
SELECT
  timestamp::time as time,
  location_name,
  activity_description,
  source_refs
FROM lifelog.events
WHERE source_type = 'iphone_photo'
  AND DATE(timestamp) = '2024-06-15'
  AND 'Daughter' = ANY(people)
ORDER BY timestamp;
```

### Example 3: All family outings in June 2024

```sql
SELECT
  DATE(timestamp) as date,
  COUNT(*) as photo_count,
  STRING_AGG(DISTINCT location_name, ', ') as locations,
  STRING_AGG(DISTINCT activity_description, '; ') as activities
FROM lifelog.events
WHERE source_type = 'iphone_photo'
  AND activity_type = 'family_outing'
  AND timestamp BETWEEN '2024-06-01' AND '2024-06-30'
GROUP BY DATE(timestamp)
ORDER BY date;
```

### Example 4: Generate daily summary for 2024-06-15

```python
def generate_daily_summary(date: str) -> str:
    """Generate narrative summary of day from photos."""

    events = db.query(
        "SELECT * FROM lifelog.events WHERE DATE(timestamp) = %s AND source_type = 'iphone_photo' ORDER BY timestamp",
        [date]
    ).fetchall()

    # Use LLM to generate narrative
    events_text = "\n".join([
        f"- {e['timestamp'].strftime('%H:%M')}: {e['activity_description']} at {e['location_name']} with {', '.join(e['people']) if e['people'] else 'alone'}"
        for e in events
    ])

    prompt = f"""
    Generate a narrative diary entry for {date} based on these verified iPhone photos:

    {events_text}

    Write in first person, past tense, as if reflecting on the day. Be concise (3-5 sentences).
    """

    response = litellm.completion(
        model="openai/chat",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

**Output**:
```
On June 15th, I started the day with breakfast at home with my daughter. We spent the
mid-morning at City Park where she played on the swings, capturing some beautiful moments.
After lunch at a downtown cafe with my spouse, we took a scenic drive and ended the day
at Alki Beach, enjoying the sunset together as a family. It was a perfect Saturday filled
with quality time.
```

---

## Integration with Dawarich

### Location Timeline Export

Dawarich needs continuous location data. Picture-pipeline provides **verified waypoints** from iPhone photos.

```python
def export_to_dawarich(start_date: str, end_date: str) -> List[dict]:
    """Export verified iPhone photo locations for Dawarich."""

    photos = db.query(Photo).filter(
        Photo.is_iphone_photo == True,
        Photo.gps_latitude != None,
        Photo.date_taken.between(start_date, end_date)
    ).order_by(Photo.date_taken).all()

    waypoints = []
    for photo in photos:
        waypoints.append({
            'timestamp': photo.date_taken.isoformat(),
            'latitude': photo.gps_latitude,
            'longitude': photo.gps_longitude,
            'accuracy': 10.0,  # iPhone GPS accuracy
            'source': 'iphone_photo',
            'confidence': 'high',
            'metadata': {
                'photo_hash': photo.sha256,
                'people': [f.person_name for f in photo.faces],
                'activity': infer_activity_type(photo.scene_description, photo.faces, photo.aesthetic_score)
            }
        })

    return waypoints
```

**Dawarich visualization** will show:
- Blue dots: GPS tracks (continuous)
- Red pins: iPhone photo locations (verified waypoints)
- Hover: Show photo thumbnail + people + activity

---

## RAG Integration: Searchable Life Memory

### Vector Embeddings

Generate embeddings for semantic search:

```python
def generate_event_embedding(event: dict) -> List[float]:
    """Generate embedding for life-log event."""

    # Combine all context
    text = f"""
    Date: {event['timestamp'].strftime('%Y-%m-%d %H:%M')}
    Location: {event['location_name']}
    People: {', '.join(event['people'])}
    Activity: {event['activity_description']}
    Scene: {event['metadata']['scene_description']}
    """

    # Generate embedding via LiteLLM
    response = litellm.embedding(
        model="openai/embed",
        input=text
    )

    return response['data'][0]['embedding']
```

### Semantic Search Examples

```python
# Query: "When did I last go to the beach with my daughter?"
results = vector_search(
    query="beach with daughter",
    filter={'source_type': 'iphone_photo', 'people': ['Daughter']},
    limit=5
)

# Query: "Family dinners in December 2024"
results = vector_search(
    query="family dinner meal",
    filter={
        'activity_type': 'meal',
        'timestamp': {'$gte': '2024-12-01', '$lte': '2024-12-31'}
    },
    limit=10
)

# Query: "What was I doing when I took photos at City Park?"
results = vector_search(
    query="City Park activities",
    filter={'location_name': {'$like': '%City Park%'}},
    limit=20
)
```

---

## Obsidian Vault: Daily Diary Pages

### Auto-Generated Daily Notes

```markdown
# 2024-06-15 Saturday

## Summary
Perfect Saturday with family - park visit, lunch downtown, beach sunset.

## Timeline

### 08:30 - Breakfast at Home
![](photos/2024/06/15/abc123.jpg)
- **People**: Daughter
- **Activity**: Morning meal
- **Location**: Home kitchen

### 10:15 - City Park Visit
![](photos/2024/06/15/def456.jpg) ![](photos/2024/06/15/ghi789.jpg)
- **People**: Daughter
- **Activity**: Family outing
- **Location**: City Park
- **Notes**: Beautiful weather, daughter loved the swings

### 12:45 - Lunch Downtown
![](photos/2024/06/15/jkl012.jpg)
- **People**: Daughter, Spouse
- **Activity**: Meal
- **Location**: Downtown cafe

### 17:00 - Beach Sunset
![](photos/2024/06/15/pqr678.jpg)
- **People**: Daughter, Spouse
- **Activity**: Family outing
- **Location**: Alki Beach
- **Notes**: Stunning sunset, perfect end to the day

## Stats
- **Total Photos**: 6
- **Locations**: 4 (Home, City Park, Downtown, Alki Beach)
- **People**: Daughter (4 photos), Spouse (2 photos)
- **Activity Types**: Meal (2), Family outing (3), Travel (1)

## Related
- [[2024-06-14|Previous Day]]
- [[2024-06-16|Next Day]]
- [[City Park|Location]]
- [[Daughter|Person]]
```

---

## Architecture: picture-pipeline → life-log

```
┌─────────────────────────────────────────────────────────┐
│ picture-pipeline (Source of Truth)                      │
│                                                           │
│ • iPhone photo verification                             │
│ • Face recognition (Daughter, Spouse, Family)          │
│ • Location extraction (GPS)                              │
│ • Scene description (AI)                                 │
│ • Activity inference (AI)                                │
└─────────────────────────────────────────────────────────┘
                          ↓ Export events
┌─────────────────────────────────────────────────────────┐
│ life-log (Aggregation)                                   │
│                                                           │
│ • Store events from ALL sources:                        │
│   - iPhone photos (highest confidence)                  │
│   - Calendar events                                      │
│   - GPS tracks                                           │
│   - WhatsApp chats                                       │
│   - Browser history                                      │
│   - Email archives                                       │
│                                                           │
│ • Correlate events by time/location                     │
│ • Generate daily summaries                               │
│ • Semantic search across all data                        │
└─────────────────────────────────────────────────────────┘
                          ↓ Generate outputs
┌─────────────────────────────────────────────────────────┐
│ Outputs                                                   │
│                                                           │
│ • Obsidian vault (daily diary pages)                    │
│ • Dawarich (location timeline)                           │
│ • Semantic search API                                    │
│ • Weekly/monthly/yearly summaries                        │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1: Core Export (Week 1)
- ✅ Export iPhone photos to lifelog.events
- ✅ Activity type inference
- ✅ Basic queries (daily timeline)

### Phase 2: Enrichment (Week 2)
- ✅ Scene descriptions via AI
- ✅ Activity descriptions
- ✅ Dawarich location export

### Phase 3: RAG Integration (Week 3)
- ✅ Vector embeddings
- ✅ Semantic search
- ✅ Obsidian vault generation

### Phase 4: Correlation (Week 4)
- ✅ Correlate with calendar events
- ✅ Correlate with GPS tracks
- ✅ Correlate with WhatsApp/email
- ✅ Generate comprehensive daily summaries

---

## Benefits

### 1. Definitive Proof
- ✅ iPhone photos = legal/personal proof
- ✅ "I was there" with GPS + timestamp
- ✅ "Who I was with" via face recognition

### 2. Automatic Diary
- ✅ No manual entry needed
- ✅ Reverse-engineered from photos
- ✅ More accurate than memory

### 3. Searchable Life Memory
- ✅ "When did I last...?"
- ✅ "What was I doing when...?"
- ✅ "Where did we go in...?"

### 4. Family History
- ✅ Track daughter's activities over time
- ✅ "What she did on X day, with whom"
- ✅ Generate yearly retrospectives

### 5. Location Insights
- ✅ Visualize movements over time (Dawarich)
- ✅ Discover patterns (frequent locations)
- ✅ Travel history

---

## Next Steps

1. Implement event export to life-log
2. Test activity inference on real photos
3. Generate first daily summary
4. Integrate with Dawarich
5. Build Obsidian vault generator
