#!/usr/bin/env python3
"""Analyze NAS photos to detect camera-taken vs downloaded/saved patterns."""

import subprocess
import json
from pathlib import Path
from collections import defaultdict
import random

def extract_metadata(photo_path: Path) -> dict:
    """Extract metadata using exiftool."""
    try:
        result = subprocess.run(
            ["exiftool", "-j", "-G", str(photo_path)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data[0] if data else {}
        return {}
    except Exception as e:
        print(f"Error extracting {photo_path}: {e}")
        return {}

def classify_photo(metadata: dict) -> dict:
    """Classify photo based on metadata patterns."""

    classification = {
        "type": "unknown",
        "confidence": 0.0,
        "indicators": {}
    }

    # Check for camera metadata
    has_fnumber = metadata.get("EXIF:FNumber") is not None
    has_exposure = metadata.get("EXIF:ExposureTime") is not None
    has_iso = metadata.get("EXIF:ISO") is not None
    has_camera_model = "iPhone" in str(metadata.get("EXIF:Model", ""))
    has_gps_temporal = (
        metadata.get("EXIF:GPSDateStamp") is not None and
        metadata.get("EXIF:GPSTimeStamp") is not None
    )

    # Check for download/save indicators
    software = str(metadata.get("EXIF:Software", ""))
    image_desc = str(metadata.get("EXIF:ImageDescription", ""))
    user_comment = str(metadata.get("EXIF:UserComment", ""))
    xmp_album = str(metadata.get("XMP:Album", ""))
    iptc_keywords = metadata.get("IPTC:Keywords", [])

    # Look for URLs or platform indicators
    all_text = f"{software} {image_desc} {user_comment} {xmp_album} {iptc_keywords}".lower()

    download_keywords = {
        "twitter": "twitter",
        "x.com": "twitter",
        "instagram": "instagram",
        "facebook": "facebook",
        "reddit": "reddit",
        "telegram": "telegram",
        "whatsapp": "whatsapp",
        "saved from": "saved",
        "download": "download",
        "http": "url"
    }

    detected_sources = []
    for keyword, source in download_keywords.items():
        if keyword in all_text:
            detected_sources.append(source)

    # Screenshot detection
    is_screenshot = (
        software == "iOS" and
        not has_fnumber and
        not has_exposure
    )

    # Classification logic
    camera_score = sum([
        has_fnumber * 0.3,
        has_exposure * 0.2,
        has_iso * 0.1,
        has_camera_model * 0.2,
        has_gps_temporal * 0.2
    ])

    if camera_score >= 0.7:
        classification["type"] = "camera_taken"
        classification["confidence"] = camera_score
        classification["indicators"] = {
            "has_camera_settings": has_fnumber,
            "has_gps_temporal": has_gps_temporal,
            "camera_model": metadata.get("EXIF:Model")
        }

    elif is_screenshot:
        classification["type"] = "screenshot"
        classification["confidence"] = 0.8
        classification["indicators"] = {
            "software": software,
            "no_camera_metadata": not has_fnumber
        }

    elif detected_sources:
        classification["type"] = "downloaded_saved"
        classification["confidence"] = 0.7
        classification["indicators"] = {
            "sources": list(set(detected_sources)),
            "xmp_album": xmp_album if xmp_album else None,
            "image_description": image_desc if image_desc else None
        }

    else:
        classification["type"] = "unknown"
        classification["confidence"] = 0.3
        classification["indicators"] = {
            "has_camera_settings": has_fnumber,
            "has_gps": has_gps_temporal,
            "software": software
        }

    return classification

def analyze_nas_photos(nas_path: Path, sample_size: int = 200):
    """Analyze sample of NAS photos."""

    print(f"Scanning NAS: {nas_path}")

    # Find all HEIC photos
    all_photos = list(nas_path.glob("**/*.heic")) + list(nas_path.glob("**/*.HEIC"))

    if not all_photos:
        print(f"No photos found in {nas_path}")
        return

    print(f"Found {len(all_photos)} photos total")

    # Sample randomly
    sample_photos = random.sample(all_photos, min(sample_size, len(all_photos)))
    print(f"Analyzing {len(sample_photos)} random samples...\n")

    # Analyze each photo
    results = defaultdict(list)

    for i, photo_path in enumerate(sample_photos, 1):
        if i % 20 == 0:
            print(f"Progress: {i}/{len(sample_photos)}")

        metadata = extract_metadata(photo_path)
        if not metadata:
            continue

        classification = classify_photo(metadata)

        results[classification["type"]].append({
            "path": str(photo_path.relative_to(nas_path)),
            "confidence": classification["confidence"],
            "indicators": classification["indicators"],
            "file_size": photo_path.stat().st_size,
            "year": photo_path.parent.parent.name if len(photo_path.parts) > 2 else "unknown"
        })

    # Print summary
    print("\n" + "="*70)
    print("ANALYSIS RESULTS")
    print("="*70)

    total = sum(len(photos) for photos in results.values())

    for photo_type, photos in sorted(results.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(photos)
        percentage = (count / total * 100) if total > 0 else 0

        print(f"\n{photo_type.upper()}: {count} photos ({percentage:.1f}%)")
        print("-" * 70)

        # Show examples
        examples = photos[:3]
        for example in examples:
            print(f"  Example: {example['path']}")
            print(f"    Confidence: {example['confidence']:.2f}")
            print(f"    Indicators: {example['indicators']}")
            print()

    # Print detailed findings for downloaded photos
    if results["downloaded_saved"]:
        print("\n" + "="*70)
        print("DOWNLOADED PHOTO METADATA PATTERNS")
        print("="*70)

        sources_found = defaultdict(int)
        albums_found = defaultdict(int)

        for photo in results["downloaded_saved"]:
            for source in photo["indicators"].get("sources", []):
                sources_found[source] += 1

            album = photo["indicators"].get("xmp_album")
            if album:
                albums_found[album] += 1

        if sources_found:
            print("\nDetected sources:")
            for source, count in sorted(sources_found.items(), key=lambda x: x[1], reverse=True):
                print(f"  {source}: {count} photos")

        if albums_found:
            print("\niOS Albums found:")
            for album, count in sorted(albums_found.items(), key=lambda x: x[1], reverse=True):
                print(f"  '{album}': {count} photos")

        # Show full metadata example
        if results["downloaded_saved"]:
            print("\nFull metadata example (first downloaded photo):")
            first_download = results["downloaded_saved"][0]
            full_path = nas_path / first_download["path"]
            print(f"  File: {first_download['path']}")

            full_metadata = extract_metadata(full_path)

            # Show relevant fields
            relevant_fields = [
                "EXIF:Software", "EXIF:ImageDescription", "EXIF:UserComment",
                "XMP:Album", "IPTC:Keywords", "IPTC:URL", "XMP:Identifier",
                "File:FileModifyDate", "EXIF:CreateDate", "EXIF:ModifyDate"
            ]

            print("\n  Metadata:")
            for field in relevant_fields:
                if field in full_metadata and full_metadata[field]:
                    print(f"    {field}: {full_metadata[field]}")

    # Save detailed results to file
    output_file = Path("/tmp/nas_photo_analysis.json")
    with open(output_file, 'w') as f:
        # Convert to serializable format
        output_data = {
            photo_type: [
                {
                    "path": p["path"],
                    "confidence": p["confidence"],
                    "indicators": p["indicators"],
                    "year": p["year"]
                }
                for p in photos
            ]
            for photo_type, photos in results.items()
        }
        json.dump(output_data, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    # Analyze icloudpd source
    nas_path = Path("/mnt/nas-photos/02-renamed-heic-from-icloudp-of-pics-i-took")

    if not nas_path.exists():
        print(f"NAS path not found: {nas_path}")
        print("Please check if NAS is mounted")
        exit(1)

    analyze_nas_photos(nas_path, sample_size=200)
