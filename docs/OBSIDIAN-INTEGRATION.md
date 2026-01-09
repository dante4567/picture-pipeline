# Obsidian Daily Note Integration

Automatically show photos from this day in past years within Obsidian daily notes.

---

## Concept: "On This Day" in Daily Notes

### Example Daily Note (2025-04-09)

```markdown
# 2025-04-09 Monday

## Photos from this day in past years

### 3 years ago (2022-04-09)
![[photo://2022-04-09/75820de3.jpg]]
*Daughter at the beach (age 21 months)*
- Location: Cologne, Germany
- Quality: 8.5/10

![[photo://2022-04-09/a61bb03b.jpg]]
*Family picnic in park*
- Quality: 8.2/10

### 5 years ago (2020-04-09)
![[photo://2020-04-09/c7f9e2a1.jpg]]
*Birthday celebration*
- Quality: 8.9/10

### 12 years ago (2013-04-09)
![[photo://2013-04-09/d16ff841.jpg]]
*Hiking trip*
- Quality: 7.8/10

---

## Today's tasks
- [ ] ...
```

---

## Implementation Strategy

### 1. Database Query for "On This Day"

```sql
-- Find photos from this day in past years
SELECT
    i.file_path,
    i.date_taken,
    i.aesthetic_score,
    i.caption,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, i.date_taken::date)) AS years_ago,
    STRING_AGG(f.person_name, ', ') AS people,
    i.metadata->>'location_name' AS location
FROM photos.images i
LEFT JOIN photos.faces f ON f.photo_id = i.id
WHERE
    -- Same month and day, different years
    EXTRACT(MONTH FROM i.date_taken) = EXTRACT(MONTH FROM CURRENT_DATE)
    AND EXTRACT(DAY FROM i.date_taken) = EXTRACT(DAY FROM CURRENT_DATE)
    AND i.date_taken::date < CURRENT_DATE  -- Past years only
    AND i.aesthetic_score >= 7.0  -- Quality filter
    AND i.is_iphone_photo = TRUE  -- Photos you took (not downloaded)
GROUP BY i.id, i.file_path, i.date_taken, i.aesthetic_score, i.caption
ORDER BY years_ago ASC, i.aesthetic_score DESC;
```

### 2. Generate Obsidian Markdown

```python
# src/integrations/obsidian.py

from pathlib import Path
from datetime import date, timedelta
from typing import List
import psycopg2

class ObsidianDailyNote:
    """Generate Obsidian daily note with photo memories."""

    def __init__(self, db_conn, vault_path: Path):
        self.db = db_conn
        self.vault_path = vault_path
        self.photos_dir = vault_path / "photos"

    def generate_daily_note(self, target_date: date) -> Path:
        """Generate or update daily note with photos from this day."""

        # Get photos from this day in past years
        photos = self.get_photos_for_date(target_date)

        # Group by years ago
        photos_by_year = {}
        for photo in photos:
            years_ago = photo['years_ago']
            if years_ago not in photos_by_year:
                photos_by_year[years_ago] = []
            photos_by_year[years_ago].append(photo)

        # Generate markdown
        note_path = self.vault_path / "Daily Notes" / f"{target_date.isoformat()}.md"

        # Create/update note
        if note_path.exists():
            content = note_path.read_text()
            # Remove old photo section
            content = self.remove_photo_section(content)
        else:
            content = f"# {target_date.isoformat()} {target_date.strftime('%A')}\n\n"

        # Add photo section
        photo_section = self.generate_photo_section(photos_by_year, target_date)
        content = content + "\n\n" + photo_section

        note_path.write_text(content)
        return note_path

    def get_photos_for_date(self, target_date: date) -> List[dict]:
        """Query photos from this day in past years."""

        query = """
        SELECT
            i.sha256_hash,
            i.date_taken,
            i.aesthetic_score,
            i.caption,
            EXTRACT(YEAR FROM AGE(%s, i.date_taken::date)) AS years_ago,
            STRING_AGG(f.person_name, ', ') AS people,
            i.metadata->>'location_name' AS location,
            CONCAT('/mnt/nas/photos/originals/',
                   TO_CHAR(i.date_taken, 'YYYY/YYYY-MM'), '/pictures/',
                   i.sha256_hash, '.heic') AS file_path
        FROM photos.images i
        LEFT JOIN photos.faces f ON f.photo_id = i.id
        WHERE
            EXTRACT(MONTH FROM i.date_taken) = %s
            AND EXTRACT(DAY FROM i.date_taken) = %s
            AND i.date_taken::date < %s
            AND i.aesthetic_score >= 7.0
            AND i.is_iphone_photo = TRUE
        GROUP BY i.id, i.sha256_hash, i.date_taken, i.aesthetic_score, i.caption
        ORDER BY years_ago ASC, i.aesthetic_score DESC
        LIMIT 20;
        """

        cursor = self.db.cursor()
        cursor.execute(query, (target_date, target_date.month, target_date.day, target_date))

        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def generate_photo_section(self, photos_by_year: dict, target_date: date) -> str:
        """Generate markdown section with photos grouped by years ago."""

        section = "## Photos from this day in past years\n\n"

        for years_ago in sorted(photos_by_year.keys()):
            year = target_date.year - years_ago
            section += f"### {years_ago} years ago ({year})\n\n"

            for photo in photos_by_year[years_ago]:
                # Copy thumbnail to Obsidian vault
                thumb_name = f"{photo['sha256_hash']}.jpg"
                thumb_src = Path(f"~/.local/share/pictures/thumbs/small/{thumb_name}").expanduser()
                thumb_dest = self.photos_dir / thumb_name

                if thumb_src.exists() and not thumb_dest.exists():
                    import shutil
                    shutil.copy(thumb_src, thumb_dest)

                # Generate markdown
                section += f"![[{thumb_name}]]\n"

                if photo['caption']:
                    section += f"*{photo['caption']}*\n"

                details = []
                if photo['people']:
                    details.append(f"People: {photo['people']}")
                if photo['location']:
                    details.append(f"Location: {photo['location']}")
                details.append(f"Quality: {photo['aesthetic_score']:.1f}/10")

                section += "- " + "\n- ".join(details) + "\n\n"

        section += "---\n"
        return section

    def remove_photo_section(self, content: str) -> str:
        """Remove existing photo section from note."""
        # Find photo section markers
        start_marker = "## Photos from this day in past years"
        end_marker = "---"

        if start_marker not in content:
            return content

        start_idx = content.find(start_marker)
        # Find the end marker after the start
        end_idx = content.find(end_marker, start_idx)

        if end_idx != -1:
            # Remove section including the end marker
            return content[:start_idx] + content[end_idx + len(end_marker):]

        return content[:start_idx]


# CLI command
def cli_generate_daily_note(date_str: str = None):
    """Generate daily note with photos."""

    target_date = date.fromisoformat(date_str) if date_str else date.today()

    db = psycopg2.connect("dbname=ragdb user=postgres")
    vault_path = Path("~/obsidian/vault").expanduser()

    obsidian = ObsidianDailyNote(db, vault_path)
    note_path = obsidian.generate_daily_note(target_date)

    print(f"✅ Generated daily note: {note_path}")
    print(f"   Photos from this day in past years added")


# Automation: Run daily via cron
# 0 6 * * * cd /home/user/picture-pipeline && ./run.sh obsidian-daily-note
```

---

## Automation Options

### 1. Cron Job (Daily)

```bash
# /etc/cron.d/picture-pipeline-obsidian
# Run every day at 6 AM
0 6 * * * user cd /home/user/picture-pipeline && ./run.sh obsidian-daily-note >> /var/log/obsidian-sync.log 2>&1
```

### 2. Obsidian Plugin (Real-time)

Create custom Obsidian plugin that calls picture-pipeline API:

```javascript
// obsidian-picture-pipeline-plugin/main.js

module.exports = class PicturePipelinePlugin {
    async onload() {
        // Add command to refresh photos
        this.addCommand({
            id: 'refresh-daily-photos',
            name: 'Refresh photos from this day',
            callback: async () => {
                await this.refreshDailyPhotos();
            }
        });

        // Auto-refresh when opening daily note
        this.registerEvent(
            this.app.workspace.on('file-open', async (file) => {
                if (this.isDailyNote(file)) {
                    await this.refreshDailyPhotos();
                }
            })
        );
    }

    async refreshDailyPhotos() {
        // Call picture-pipeline CLI
        const { exec } = require('child_process');

        exec('cd ~/picture-pipeline && ./run.sh obsidian-daily-note',
             (error, stdout, stderr) => {
                 if (error) {
                     new Notice(`Error refreshing photos: ${error.message}`);
                     return;
                 }
                 new Notice('Photos refreshed!');
             });
    }

    isDailyNote(file) {
        // Check if filename matches YYYY-MM-DD pattern
        return /^\d{4}-\d{2}-\d{2}\.md$/.test(file.name);
    }
};
```

---

## Advanced Features

### 1. Milestone Dates

Show photos from significant dates (daughter's birthdays, anniversaries):

```python
def get_milestone_photos(target_date: date) -> List[dict]:
    """Get photos from significant dates related to target date."""

    # Example: Daughter's birthday is 2020-06-15
    daughter_birthday = date(2020, 6, 15)

    if target_date.month == daughter_birthday.month and target_date.day == daughter_birthday.day:
        # Show all birthday photos
        return query_photos_by_date(
            month=daughter_birthday.month,
            day=daughter_birthday.day,
            person='daughter'
        )

    return []
```

### 2. Best Photo of the Week

```markdown
## Best photos this week

### Top 5 photos from this week in past years
![[photo1.jpg]]
*Score: 9.2/10 - Family vacation, 3 years ago*

![[photo2.jpg]]
*Score: 8.9/10 - Daughter's first steps, 5 years ago*
```

### 3. Location-Based Memories

```markdown
## Photos from Cologne, Germany

You've taken 45 photos in this location over the years:
- 2023-04-09: Beach day with daughter (8.5/10)
- 2022-07-15: Park picnic (8.2/10)
- 2021-03-10: City walk (7.9/10)
```

---

## CLI Commands

```bash
# Generate today's daily note
./run.sh obsidian-daily-note

# Generate note for specific date
./run.sh obsidian-daily-note 2025-04-09

# Regenerate all daily notes (backfill)
./run.sh obsidian-backfill --start 2020-01-01 --end 2025-12-31

# Test query (dry run)
./run.sh obsidian-preview 2025-04-09
```

---

## Configuration

```yaml
# ~/.config/picture-pipeline/obsidian.yml

obsidian:
  vault_path: ~/obsidian/vault
  daily_notes_path: Daily Notes
  photos_dir: photos

  photo_section:
    min_quality: 7.0
    max_photos_per_year: 3
    include_captions: true
    include_people: true
    include_location: true

  milestones:
    - name: daughter_birthday
      date: 2020-06-15
      person: daughter
    - name: wedding_anniversary
      date: 2015-08-20
```

---

## Example Output (Full Daily Note)

```markdown
# 2025-04-09 Monday

## Photos from this day in past years

### 3 years ago (2022)
![[75820de3.jpg]]
*A smiling toddler girl playing with sand on a sunny beach*
- People: daughter, spouse
- Location: Cologne, Germany
- Quality: 8.5/10

![[a61bb03b.jpg]]
*Family enjoying picnic in park*
- People: daughter, spouse, grandparent
- Location: Nice, France
- Quality: 8.2/10

### 5 years ago (2020)
![[c7f9e2a1.jpg]]
*Birthday celebration with family*
- People: daughter, family
- Location: Berlin, Germany
- Quality: 8.9/10

### 12 years ago (2013)
![[d16ff841.jpg]]
*Hiking trip in the mountains*
- People: spouse, friend
- Location: Swiss Alps
- Quality: 7.8/10

---

## Today's Schedule
- [ ] Morning meeting at 9 AM
- [ ] Lunch with team
- [ ] Finish project documentation

## Notes
...
```

---

**Next**: Implement Raspberry Pi picture frame integration for displaying best photos!
