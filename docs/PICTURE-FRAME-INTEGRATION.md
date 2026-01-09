# Digital Picture Frame Integration

Display best photos since daughter was born on Raspberry Pi or digital picture frame.

---

## Concept: "Best Memories" Display

### Use Cases

1. **Daily rotation** - Show best photo of each day since daughter was born
2. **Weekly highlights** - Top 5 photos from this week in past years
3. **Milestone timeline** - Photos showing daughter's growth month by month
4. **"On this day"** - Photos from this date in past years

---

## Hardware Options

### Option 1: Raspberry Pi + HDMI Display

```
Raspberry Pi 4 (2GB+)
  ↓ HDMI
7-10" touchscreen or TV
  ↓ Power
USB-C power supply
```

**Cost**: ~$100-150

### Option 2: Dedicated Picture Frame

- **Nixplay** - Cloud-connected, email photos
- **Aura** - Unlimited storage, app control
- **Skylight** - Touchscreen, calendar integration

**Cost**: ~$150-300

### Option 3: Old Tablet + Kiosk App

- Repurpose old iPad/Android tablet
- Mount on wall
- Run kiosk app (Fully Kiosk Browser, etc.)

**Cost**: Free (reuse existing)

---

## Architecture

```
picture-pipeline (Database)
  ↓ Query best photos
picture-frame-server (Python/Flask)
  ↓ Serve photos API
Raspberry Pi (Display client)
  ↓ Fetch + display
HDMI screen
```

---

## Implementation

### 1. Photo Selection Query

```sql
-- Get best photos since daughter was born, one per day
WITH daughter_photos AS (
    SELECT
        i.sha256_hash,
        i.date_taken::date AS photo_date,
        i.aesthetic_score,
        i.caption,
        f.age_months,
        ROW_NUMBER() OVER (
            PARTITION BY i.date_taken::date
            ORDER BY i.aesthetic_score DESC
        ) AS rank_per_day
    FROM photos.images i
    JOIN photos.faces f ON f.photo_id = i.id
    JOIN photos.people p ON p.id = f.person_id
    WHERE p.name = 'daughter'
      AND i.date_taken >= '2020-06-15'  -- Daughter's birthdate
      AND i.aesthetic_score >= 7.0
      AND i.is_iphone_photo = TRUE
)
SELECT
    sha256_hash,
    photo_date,
    aesthetic_score,
    caption,
    age_months
FROM daughter_photos
WHERE rank_per_day = 1  -- Best photo of each day
ORDER BY photo_date;
```

**Result**: ~1,800 photos (one per day since birth, 5 years = ~1,825 days)

---

### 2. Picture Frame Server

```python
# src/integrations/picture_frame_server.py

from flask import Flask, jsonify, send_file
from pathlib import Path
import psycopg2
from datetime import date, timedelta

app = Flask(__name__)

class PictureFrameServer:
    """Serve photos for digital picture frame."""

    def __init__(self, db_conn):
        self.db = db_conn

    def get_daily_rotation(self) -> list:
        """Get photos for daily rotation (one best photo per day)."""

        query = """
        WITH daughter_photos AS (
            SELECT
                i.sha256_hash,
                i.date_taken::date AS photo_date,
                i.aesthetic_score,
                i.caption,
                f.age_months,
                ROW_NUMBER() OVER (
                    PARTITION BY i.date_taken::date
                    ORDER BY i.aesthetic_score DESC
                ) AS rank_per_day
            FROM photos.images i
            JOIN photos.faces f ON f.photo_id = i.id
            JOIN photos.people p ON p.id = f.person_id
            WHERE p.name = 'daughter'
              AND i.date_taken >= %s
              AND i.aesthetic_score >= 7.0
        )
        SELECT sha256_hash, photo_date, aesthetic_score, caption, age_months
        FROM daughter_photos
        WHERE rank_per_day = 1
        ORDER BY photo_date;
        """

        cursor = self.db.cursor()
        cursor.execute(query, ('2020-06-15',))  # Daughter's birthdate

        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_on_this_day(self, target_date: date) -> list:
        """Get photos from this day in past years."""

        query = """
        SELECT
            i.sha256_hash,
            i.date_taken,
            i.aesthetic_score,
            i.caption,
            f.age_months,
            EXTRACT(YEAR FROM AGE(%s, i.date_taken::date)) AS years_ago
        FROM photos.images i
        JOIN photos.faces f ON f.photo_id = i.id
        JOIN photos.people p ON p.id = f.person_id
        WHERE p.name = 'daughter'
          AND EXTRACT(MONTH FROM i.date_taken) = %s
          AND EXTRACT(DAY FROM i.date_taken) = %s
          AND i.date_taken::date < %s
          AND i.aesthetic_score >= 7.0
        ORDER BY years_ago ASC, i.aesthetic_score DESC
        LIMIT 10;
        """

        cursor = self.db.cursor()
        cursor.execute(query, (target_date, target_date.month, target_date.day, target_date))

        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


# Flask API routes
server = PictureFrameServer(psycopg2.connect("dbname=ragdb user=postgres"))

@app.route('/api/photos/daily-rotation')
def api_daily_rotation():
    """Get all photos for daily rotation."""
    photos = server.get_daily_rotation()
    return jsonify(photos)

@app.route('/api/photos/on-this-day')
def api_on_this_day():
    """Get photos from this day in past years."""
    photos = server.get_on_this_day(date.today())
    return jsonify(photos)

@app.route('/api/photos/thumbnail/<sha256>')
def api_thumbnail(sha256: str):
    """Serve photo thumbnail."""
    thumb_path = Path(f"~/.local/share/pictures/thumbs/medium/{sha256}.jpg").expanduser()

    if thumb_path.exists():
        return send_file(thumb_path, mimetype='image/jpeg')
    else:
        return "Not found", 404

@app.route('/api/photos/full/<sha256>')
def api_full_photo(sha256: str):
    """Serve full resolution photo (for 1920x1080 display)."""
    thumb_path = Path(f"~/.local/share/pictures/thumbs/medium/{sha256}.jpg").expanduser()

    if thumb_path.exists():
        return send_file(thumb_path, mimetype='image/jpeg')
    else:
        return "Not found", 404


if __name__ == '__main__':
    # Run server on local network
    app.run(host='0.0.0.0', port=5000)
```

---

### 3. Raspberry Pi Display Client

```python
# raspberry-pi/picture_frame_client.py

import requests
import pygame
from pathlib import Path
from datetime import datetime
import time

class PictureFrameClient:
    """Display client for Raspberry Pi."""

    def __init__(self, server_url: str, display_size: tuple = (1920, 1080)):
        self.server_url = server_url
        self.display_size = display_size

        pygame.init()
        self.screen = pygame.display.set_mode(display_size, pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)

        self.photos = []
        self.current_index = 0

    def load_photos(self):
        """Load photo list from server."""
        response = requests.get(f"{self.server_url}/api/photos/daily-rotation")
        self.photos = response.json()
        print(f"Loaded {len(self.photos)} photos")

    def download_thumbnail(self, sha256: str) -> Path:
        """Download photo thumbnail."""
        cache_dir = Path("/tmp/picture-frame-cache")
        cache_dir.mkdir(exist_ok=True)

        thumb_path = cache_dir / f"{sha256}.jpg"

        if not thumb_path.exists():
            response = requests.get(f"{self.server_url}/api/photos/full/{sha256}")
            if response.status_code == 200:
                thumb_path.write_bytes(response.content)

        return thumb_path

    def display_photo(self, photo: dict):
        """Display photo with caption."""

        # Download thumbnail
        thumb_path = self.download_thumbnail(photo['sha256_hash'])

        if not thumb_path.exists():
            return

        # Load and scale image
        image = pygame.image.load(str(thumb_path))
        image = pygame.transform.scale(image, self.display_size)

        # Display image
        self.screen.fill((0, 0, 0))
        self.screen.blit(image, (0, 0))

        # Add caption overlay (bottom)
        font = pygame.font.SysFont('Arial', 36)

        caption_text = photo.get('caption', 'No caption')
        date_text = photo['photo_date']
        age_text = f"Age: {photo['age_months']} months" if photo['age_months'] else ""
        score_text = f"Quality: {photo['aesthetic_score']:.1f}/10"

        # Render text with background
        y_offset = self.display_size[1] - 150

        texts = [caption_text, f"{date_text} | {age_text} | {score_text}"]
        for text in texts:
            surface = font.render(text, True, (255, 255, 255))
            rect = surface.get_rect()
            rect.center = (self.display_size[0] // 2, y_offset)

            # Background rect
            bg_rect = rect.inflate(40, 20)
            pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect)

            self.screen.blit(surface, rect)
            y_offset += 50

        pygame.display.flip()

    def run(self, interval_seconds: int = 30):
        """Run picture frame display loop."""

        self.load_photos()

        running = True
        last_change = time.time()

        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        running = False
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_SPACE:
                        self.current_index = (self.current_index + 1) % len(self.photos)
                        last_change = time.time()
                    elif event.key == pygame.K_LEFT:
                        self.current_index = (self.current_index - 1) % len(self.photos)
                        last_change = time.time()

            # Auto-advance
            if time.time() - last_change >= interval_seconds:
                self.current_index = (self.current_index + 1) % len(self.photos)
                last_change = time.time()

            # Display current photo
            if self.photos:
                self.display_photo(self.photos[self.current_index])

            time.sleep(0.1)

        pygame.quit()


if __name__ == '__main__':
    # Server running on main machine
    client = PictureFrameClient(
        server_url="http://192.168.1.100:5000",
        display_size=(1920, 1080)
    )

    # Show photo every 30 seconds
    client.run(interval_seconds=30)
```

---

## Deployment

### On Main Machine (Server)

```bash
# Start picture frame server
cd ~/picture-pipeline
./run.sh picture-frame-server

# Runs on http://0.0.0.0:5000
# Accessible from local network: http://192.168.1.100:5000
```

### On Raspberry Pi (Client)

```bash
# Install dependencies
sudo apt install python3-pygame python3-requests

# Download client script
wget https://raw.githubusercontent.com/user/picture-pipeline/main/raspberry-pi/picture_frame_client.py

# Configure server URL
nano picture_frame_client.py
# Change: server_url="http://192.168.1.100:5000"

# Run on boot (systemd service)
sudo tee /etc/systemd/system/picture-frame.service <<EOF
[Unit]
Description=Picture Frame Display
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/picture_frame_client.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable picture-frame
sudo systemctl start picture-frame
```

---

## Features

### 1. Rotation Modes

```python
class RotationMode:
    DAILY = "daily"              # One best photo per day
    ON_THIS_DAY = "on_this_day"  # Photos from this day in past years
    WEEKLY_BEST = "weekly_best"  # Top 5 of each week
    MILESTONES = "milestones"    # Monthly growth timeline
    RANDOM = "random"            # Random high-quality photos
```

### 2. Touchscreen Controls

- **Tap left** → Previous photo
- **Tap right** → Next photo
- **Double tap** → Toggle captions
- **Long press** → Switch rotation mode

### 3. Time-Based Display

```python
# Show "On This Day" photos in the morning (6 AM - 12 PM)
# Show daily rotation rest of the day

current_hour = datetime.now().hour

if 6 <= current_hour < 12:
    photos = server.get_on_this_day(date.today())
else:
    photos = server.get_daily_rotation()
```

---

## Advanced Features

### 1. Growth Timeline View

Show daughter's face at same age in different photos:

```
Age 12 months    Age 18 months    Age 24 months
[Photo 1]        [Photo 2]        [Photo 3]
Dec 2021         Jun 2022         Dec 2022
```

### 2. Location-Based Memories

Group photos by location:

```
Cologne, Germany (45 photos)
Nice, France (23 photos)
Berlin, Germany (18 photos)
```

### 3. Voice Control (with USB mic)

```python
# "Show photos from last summer"
# "Show daughter's birthday photos"
# "Show beach photos"
```

---

## Hardware Setup

### Raspberry Pi 4 Picture Frame

```
Components:
- Raspberry Pi 4 (2GB) - $45
- 7" touchscreen display - $60
- SD card (32GB) - $10
- Power supply - $15
- Picture frame case - $20
────────────────────────
Total: ~$150
```

### Assembly:
1. Flash Raspberry Pi OS Lite to SD card
2. Connect touchscreen to Raspberry Pi
3. Mount in picture frame case
4. Configure auto-start on boot

---

## Configuration

```yaml
# ~/.config/picture-pipeline/picture-frame.yml

picture_frame:
  server_url: http://192.168.1.100:5000
  display_size: [1920, 1080]
  rotation_interval: 30  # seconds

  filters:
    person: daughter
    min_quality: 7.0
    since_date: 2020-06-15

  rotation_modes:
    - daily
    - on_this_day
    - weekly_best

  schedule:
    morning_mode: on_this_day  # 6 AM - 12 PM
    default_mode: daily        # Rest of day
```

---

## CLI Commands

```bash
# Start picture frame server
./run.sh picture-frame-server

# Test API
curl http://localhost:5000/api/photos/daily-rotation | jq

# Deploy to Raspberry Pi
./run.sh deploy-picture-frame --host 192.168.1.50
```

---

**Result**: Wall-mounted picture frame showing best memories since daughter was born, rotating every 30 seconds! 📸✨
