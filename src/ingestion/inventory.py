#!/usr/bin/env python3
"""Photo source inventory scanner.

Discovers all photo sources on the system and generates inventory report.
This is the FIRST STEP in consolidation - understanding what you have where.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import hashlib
from datetime import datetime


@dataclass
class PhotoSource:
    """Information about a photo source."""
    name: str
    path: str
    exists: bool
    count: int
    size_bytes: int
    size_gb: float
    formats: Dict[str, int]  # {extension: count}
    sample_files: List[str]  # First 5 files as examples
    has_metadata: bool  # XMP sidecars, databases, etc.
    notes: str


@dataclass
class InventoryReport:
    """Complete inventory of all photo sources."""
    scan_date: str
    sources: List[PhotoSource]
    total_photos: int
    total_size_gb: float
    unique_formats: List[str]
    estimated_duplicates: Optional[int] = None
    estimated_unique: Optional[int] = None
    estimated_after_dedup_gb: Optional[float] = None


class PhotoInventory:
    """Scan all potential photo sources and generate inventory."""

    # Image extensions to search for
    PHOTO_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.heic', '.heif',
        '.raw', '.cr2', '.nef', '.arw', '.dng',
        '.gif', '.bmp', '.tiff', '.webp'
    }

    VIDEO_EXTENSIONS = {
        '.mp4', '.mov', '.m4v', '.hevc', '.avi',
        '.mkv', '.webm', '.3gp'
    }

    ALL_EXTENSIONS = PHOTO_EXTENSIONS | VIDEO_EXTENSIONS

    def __init__(self):
        """Initialize inventory scanner."""
        self.sources: List[PhotoSource] = []

    def scan_directory(self, path: Path, max_files: int = 10000) -> Dict:
        """Scan a directory for photos and videos.

        Args:
            path: Directory to scan
            max_files: Maximum files to scan (for performance)

        Returns:
            Dict with count, size, formats, samples
        """
        if not path.exists():
            return {
                'count': 0,
                'size_bytes': 0,
                'formats': {},
                'samples': []
            }

        count = 0
        size_bytes = 0
        formats = Counter()
        samples = []

        # Recursively find all media files
        for ext in self.ALL_EXTENSIONS:
            for file_path in path.rglob(f"*{ext}"):
                if count >= max_files:
                    break

                try:
                    file_size = file_path.stat().st_size
                    size_bytes += file_size
                    formats[ext] += 1
                    count += 1

                    # Collect samples
                    if len(samples) < 5:
                        samples.append(str(file_path.relative_to(path)))

                except (OSError, PermissionError):
                    continue

        return {
            'count': count,
            'size_bytes': size_bytes,
            'formats': dict(formats),
            'samples': samples
        }

    def check_icloud_photos(self) -> PhotoSource:
        """Check iCloud Photos library."""
        # Common iCloud Photos locations
        possible_paths = [
            Path.home() / "Pictures" / "iCloud Photos",
            Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Photos",
            Path("/mnt/nas/iCloud"),
        ]

        for path in possible_paths:
            if path.exists():
                result = self.scan_directory(path)
                return PhotoSource(
                    name="iCloud Photos",
                    path=str(path),
                    exists=True,
                    count=result['count'],
                    size_bytes=result['size_bytes'],
                    size_gb=round(result['size_bytes'] / (1024**3), 2),
                    formats=result['formats'],
                    sample_files=result['samples'],
                    has_metadata=True,
                    notes="Original iPhone photos with full EXIF metadata. HIGHEST PRIORITY for import."
                )

        return PhotoSource(
            name="iCloud Photos",
            path="Not found",
            exists=False,
            count=0,
            size_bytes=0,
            size_gb=0.0,
            formats={},
            sample_files=[],
            has_metadata=False,
            notes="Not found on this system"
        )

    def check_digikam(self) -> PhotoSource:
        """Check digiKam library."""
        # Common digiKam locations
        possible_paths = [
            Path("/mnt/nas/Photos/digikam"),
            Path("/mnt/nas/photos/digikam"),
            Path.home() / "Pictures" / "digikam",
        ]

        for path in possible_paths:
            if path.exists():
                result = self.scan_directory(path)

                # Check for XMP sidecars
                xmp_count = len(list(path.rglob("*.xmp")))
                has_metadata = xmp_count > 0

                return PhotoSource(
                    name="digiKam Library",
                    path=str(path),
                    exists=True,
                    count=result['count'],
                    size_bytes=result['size_bytes'],
                    size_gb=round(result['size_bytes'] / (1024**3), 2),
                    formats=result['formats'],
                    sample_files=result['samples'],
                    has_metadata=has_metadata,
                    notes=f"Desktop organization with albums/tags. XMP sidecars: {xmp_count}. SECOND PRIORITY."
                )

        return PhotoSource(
            name="digiKam Library",
            path="Not found",
            exists=False,
            count=0,
            size_bytes=0,
            size_gb=0.0,
            formats={},
            sample_files=[],
            has_metadata=False,
            notes="Not found on this system"
        )

    def check_immich(self) -> PhotoSource:
        """Check Immich storage."""
        possible_paths = [
            Path("/mnt/nas/immich/library"),
            Path("/mnt/nas/immich-storage"),
            Path("/mnt/nas/photos/immich"),
        ]

        for path in possible_paths:
            if path.exists():
                result = self.scan_directory(path)

                return PhotoSource(
                    name="Immich Storage",
                    path=str(path),
                    exists=True,
                    count=result['count'],
                    size_bytes=result['size_bytes'],
                    size_gb=round(result['size_bytes'] / (1024**3), 2),
                    formats=result['formats'],
                    sample_files=result['samples'],
                    has_metadata=True,
                    notes="Self-hosted mobile backup. Check for unique uploads not in iCloud."
                )

        return PhotoSource(
            name="Immich Storage",
            path="Not found",
            exists=False,
            count=0,
            size_bytes=0,
            size_gb=0.0,
            formats={},
            sample_files=[],
            has_metadata=False,
            notes="Not found on this system"
        )

    def check_photoprism(self) -> PhotoSource:
        """Check PhotoPrism storage."""
        possible_paths = [
            Path("/mnt/nas/photoprism/originals"),
            Path("/mnt/nas/photoprism-storage"),
            Path("/mnt/nas/photos/photoprism"),
        ]

        for path in possible_paths:
            if path.exists():
                result = self.scan_directory(path)

                return PhotoSource(
                    name="PhotoPrism Storage",
                    path=str(path),
                    exists=True,
                    count=result['count'],
                    size_bytes=result['size_bytes'],
                    size_gb=round(result['size_bytes'] / (1024**3), 2),
                    formats=result['formats'],
                    sample_files=result['samples'],
                    has_metadata=True,
                    notes="Web UI with AI features. Likely many duplicates from other sources."
                )

        return PhotoSource(
            name="PhotoPrism Storage",
            path="Not found",
            exists=False,
            count=0,
            size_bytes=0,
            size_gb=0.0,
            formats={},
            sample_files=[],
            has_metadata=False,
            notes="Not found on this system"
        )

    def check_damselfly(self) -> PhotoSource:
        """Check Damselfly storage."""
        possible_paths = [
            Path("/mnt/nas/damselfly"),
            Path("/mnt/nas/photos/damselfly"),
        ]

        for path in possible_paths:
            if path.exists():
                result = self.scan_directory(path)

                return PhotoSource(
                    name="Damselfly Storage",
                    path=str(path),
                    exists=True,
                    count=result['count'],
                    size_bytes=result['size_bytes'],
                    size_gb=round(result['size_bytes'] / (1024**3), 2),
                    formats=result['formats'],
                    sample_files=result['samples'],
                    has_metadata=False,
                    notes="Tried briefly. Likely all duplicates from other sources."
                )

        return PhotoSource(
            name="Damselfly Storage",
            path="Not found",
            exists=False,
            count=0,
            size_bytes=0,
            size_gb=0.0,
            formats={},
            sample_files=[],
            has_metadata=False,
            notes="Not found on this system"
        )

    def check_google_photos(self) -> PhotoSource:
        """Check Google Photos export (if downloaded)."""
        possible_paths = [
            Path.home() / "Downloads" / "Takeout" / "Google Photos",
            Path("/mnt/nas/google-photos-export"),
        ]

        for path in possible_paths:
            if path.exists():
                result = self.scan_directory(path)

                return PhotoSource(
                    name="Google Photos Export",
                    path=str(path),
                    exists=True,
                    count=result['count'],
                    size_bytes=result['size_bytes'],
                    size_gb=round(result['size_bytes'] / (1024**3), 2),
                    formats=result['formats'],
                    sample_files=result['samples'],
                    has_metadata=True,
                    notes="Android backups. May have unique photos not in iCloud."
                )

        return PhotoSource(
            name="Google Photos Export",
            path="Not found",
            exists=False,
            count=0,
            size_bytes=0,
            size_gb=0.0,
            formats={},
            sample_files=[],
            has_metadata=False,
            notes="Not downloaded. Use takeout.google.com to export."
        )

    def check_icloud_sync(self) -> PhotoSource:
        """Check icloudSync (docker-icloud-backup) storage."""
        possible_paths = [
            Path("/mnt/nas/icloud-sync"),
            Path("/mnt/nas/docker-icloud"),
            Path("/mnt/nas/icloudpd"),
        ]

        for path in possible_paths:
            if path.exists():
                result = self.scan_directory(path)

                return PhotoSource(
                    name="icloudSync (Docker)",
                    path=str(path),
                    exists=True,
                    count=result['count'],
                    size_bytes=result['size_bytes'],
                    size_gb=round(result['size_bytes'] / (1024**3), 2),
                    formats=result['formats'],
                    sample_files=result['samples'],
                    has_metadata=True,
                    notes="Docker iCloud backup container. User reports this scored highest."
                )

        return PhotoSource(
            name="icloudSync (Docker)",
            path="Not found",
            exists=False,
            count=0,
            size_bytes=0,
            size_gb=0.0,
            formats={},
            sample_files=[],
            has_metadata=False,
            notes="Not found. Check Proxmox container status."
        )

    def check_nas_scattered(self) -> PhotoSource:
        """Check for scattered photos in NAS."""
        base_paths = [
            Path("/mnt/nas/Photos"),
            Path("/mnt/nas/Pictures"),
            Path("/mnt/nas/Backup/Photos"),
        ]

        total_count = 0
        total_size = 0
        all_formats = Counter()
        all_samples = []

        for base_path in base_paths:
            if base_path.exists():
                result = self.scan_directory(base_path, max_files=5000)
                total_count += result['count']
                total_size += result['size_bytes']
                all_formats.update(result['formats'])
                all_samples.extend(result['samples'][:2])

        if total_count > 0:
            return PhotoSource(
                name="NAS Scattered",
                path="/mnt/nas (various folders)",
                exists=True,
                count=total_count,
                size_bytes=total_size,
                size_gb=round(total_size / (1024**3), 2),
                formats=dict(all_formats),
                sample_files=all_samples[:5],
                has_metadata=False,
                notes="Old backups and unorganized folders. Check for unique photos."
            )

        return PhotoSource(
            name="NAS Scattered",
            path="Not found",
            exists=False,
            count=0,
            size_bytes=0,
            size_gb=0.0,
            formats={},
            sample_files=[],
            has_metadata=False,
            notes="No scattered photos found"
        )

    def run_inventory(self) -> InventoryReport:
        """Run complete inventory scan."""
        print("🔍 Scanning photo sources...")
        print()

        # Scan all sources
        self.sources = [
            self.check_icloud_sync(),      # User says this scored highest
            self.check_icloud_photos(),
            self.check_digikam(),
            self.check_immich(),
            self.check_photoprism(),
            self.check_damselfly(),
            self.check_google_photos(),
            self.check_nas_scattered(),
        ]

        # Calculate totals
        total_photos = sum(s.count for s in self.sources if s.exists)
        total_size_gb = sum(s.size_gb for s in self.sources if s.exists)

        # Collect all formats
        all_formats = set()
        for source in self.sources:
            all_formats.update(source.formats.keys())

        # Estimate duplicates (rough heuristic: 40-60% of total)
        # This will be refined by actual SHA256 hashing
        estimated_duplicates = int(total_photos * 0.5)
        estimated_unique = total_photos - estimated_duplicates
        estimated_after_dedup_gb = total_size_gb * 0.5

        report = InventoryReport(
            scan_date=datetime.now().isoformat(),
            sources=self.sources,
            total_photos=total_photos,
            total_size_gb=round(total_size_gb, 2),
            unique_formats=sorted(all_formats),
            estimated_duplicates=estimated_duplicates,
            estimated_unique=estimated_unique,
            estimated_after_dedup_gb=round(estimated_after_dedup_gb, 2)
        )

        return report

    def print_report(self, report: InventoryReport):
        """Print inventory report to console."""
        print("\n" + "="*80)
        print("📊 PHOTO INVENTORY REPORT")
        print("="*80)
        print(f"Scan Date: {report.scan_date}")
        print()

        print("📁 Sources Found:")
        print()

        for source in report.sources:
            if source.exists:
                print(f"✅ {source.name}")
                print(f"   Path: {source.path}")
                print(f"   Photos: {source.count:,}")
                print(f"   Size: {source.size_gb:.2f} GB")
                print(f"   Formats: {', '.join(f'{ext} ({count})' for ext, count in sorted(source.formats.items()))}")
                print(f"   Notes: {source.notes}")
                print()
            else:
                print(f"❌ {source.name} - Not found")
                print()

        print("="*80)
        print("📈 SUMMARY")
        print("="*80)
        print(f"Total Photos Found: {report.total_photos:,}")
        print(f"Total Storage Used: {report.total_size_gb:.2f} GB")
        print(f"Unique Formats: {', '.join(report.unique_formats) if report.unique_formats else 'None'}")
        print()

        if report.total_photos > 0:
            print(f"Estimated Duplicates: ~{report.estimated_duplicates:,} ({(report.estimated_duplicates/report.total_photos*100):.0f}%)")
            print(f"Estimated Unique Photos: ~{report.estimated_unique:,}")
            print(f"Estimated After Dedup: ~{report.estimated_after_dedup_gb:.2f} GB")

            savings_pct = ((report.total_size_gb - report.estimated_after_dedup_gb)/report.total_size_gb*100) if report.total_size_gb > 0 else 0
            print(f"Potential Storage Savings: ~{report.total_size_gb - report.estimated_after_dedup_gb:.2f} GB ({savings_pct:.0f}%)")
            print()
            print("⚠️  Duplicate estimates are rough. Run SHA256 hashing for accurate deduplication.")
        else:
            print("⚠️  No photos found. Check if NAS is mounted and paths are correct.")
            print()
            print("💡 To configure paths, edit src/ingestion/inventory.py:")
            print("   - Update paths in check_icloud_sync(), check_digikam(), etc.")
            print("   - Or provide your actual NAS mount point and folder structure")
        print()

    def save_report(self, report: InventoryReport, output_path: Path):
        """Save inventory report to JSON."""
        # Convert to dict
        report_dict = {
            'scan_date': report.scan_date,
            'sources': [asdict(s) for s in report.sources],
            'total_photos': report.total_photos,
            'total_size_gb': report.total_size_gb,
            'unique_formats': report.unique_formats,
            'estimated_duplicates': report.estimated_duplicates,
            'estimated_unique': report.estimated_unique,
            'estimated_after_dedup_gb': report.estimated_after_dedup_gb,
        }

        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)

        print(f"💾 Report saved to: {output_path}")


def main():
    """Run inventory scan."""
    inventory = PhotoInventory()
    report = inventory.run_inventory()
    inventory.print_report(report)

    # Save to file
    output_path = Path("inventory.json")
    inventory.save_report(report, output_path)


if __name__ == "__main__":
    main()
