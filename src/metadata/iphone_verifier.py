"""iPhone photo verification - CRITICAL for life-log proof."""
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class iPhoneVerification:
    """Result of iPhone photo verification."""
    is_iphone_photo: bool
    confidence: float  # 0.0 - 1.0
    iphone_model: Optional[str] = None
    ios_version: Optional[str] = None
    has_gps: bool = False
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_accuracy: Optional[float] = None
    is_hdr: bool = False
    is_live_photo: bool = False
    date_taken: Optional[str] = None
    reasons: list = None

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []


class iPhonePhotoVerifier:
    """Verify if photo was taken with iPhone.

    This provides LEGAL PROOF of location and time for life-log/diary.
    """

    def __init__(self):
        self._check_exiftool()

    def _check_exiftool(self):
        """Verify ExifTool is installed."""
        try:
            subprocess.run(
                ["exiftool", "-ver"],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "ExifTool not found. Install: sudo apt install libimage-exiftool-perl"
            )

    def extract_metadata(self, photo_path: Path) -> Dict:
        """Extract ALL metadata using ExifTool."""
        result = subprocess.run(
            ["exiftool", "-j", "-G", "-a", str(photo_path)],
            capture_output=True,
            text=True,
            check=True
        )

        metadata = json.loads(result.stdout)[0]
        return metadata

    def verify_iphone_photo(self, photo_path: Path) -> iPhoneVerification:
        """Verify if photo was taken with iPhone.

        Args:
            photo_path: Path to photo file

        Returns:
            iPhoneVerification with confidence and details
        """
        metadata = self.extract_metadata(photo_path)

        reasons = []
        confidence_score = 0.0

        # Check 1: Camera Make (REQUIRED)
        make = metadata.get("EXIF:Make") or metadata.get("IFD0:Make")
        if make != "Apple":
            return iPhoneVerification(
                is_iphone_photo=False,
                confidence=0.0,
                reasons=["Camera make is not Apple"]
            )

        reasons.append("✓ Camera make: Apple")
        confidence_score += 0.3

        # Check 2: Camera Model (REQUIRED)
        model = metadata.get("EXIF:Model") or metadata.get("IFD0:Model")
        if not model or not model.startswith("iPhone"):
            return iPhoneVerification(
                is_iphone_photo=False,
                confidence=confidence_score,
                reasons=reasons + ["✗ Model is not iPhone"]
            )

        reasons.append(f"✓ Camera model: {model}")
        confidence_score += 0.3

        # Check 3: Software/iOS version (HIGHLY RECOMMENDED)
        software = metadata.get("EXIF:Software") or metadata.get("IFD0:Software")
        ios_version = None
        if software and ("iOS" in software or "iPhone OS" in software):
            ios_version = software
            reasons.append(f"✓ iOS software: {software}")
            confidence_score += 0.2
        else:
            reasons.append(f"⚠ Software not iOS: {software}")
            confidence_score += 0.05  # Still possible, but less confident

        # Check 4: Apple-specific tags (STRONG INDICATOR)
        has_apple_tags = False
        apple_tags = [
            "Apple:ContentIdentifier",
            "Apple:ImageUniqueID",
            "Apple:RunTimeFlags",
        ]

        found_tags = []
        for tag in apple_tags:
            if tag in metadata:
                found_tags.append(tag)
                has_apple_tags = True

        if has_apple_tags:
            reasons.append(f"✓ Apple tags: {', '.join(found_tags)}")
            confidence_score += 0.2
        else:
            reasons.append("⚠ No Apple-specific tags found")

        # Extract GPS data (CRITICAL for life-log)
        gps_lat = self._parse_gps(metadata.get("EXIF:GPSLatitude"))
        gps_lon = self._parse_gps(metadata.get("EXIF:GPSLongitude"))
        gps_lat_ref = metadata.get("EXIF:GPSLatitudeRef")
        gps_lon_ref = metadata.get("EXIF:GPSLongitudeRef")

        # Apply GPS reference (N/S, E/W)
        if gps_lat and gps_lat_ref == "S":
            gps_lat = -gps_lat
        if gps_lon and gps_lon_ref == "W":
            gps_lon = -gps_lon

        has_gps = gps_lat is not None and gps_lon is not None

        # GPS accuracy (iPhone typically <10m)
        gps_accuracy = None
        if "EXIF:GPSHPositioningError" in metadata:
            try:
                # Format: "5.000 m" or just "5.0"
                accuracy_str = metadata["EXIF:GPSHPositioningError"]
                gps_accuracy = float(accuracy_str.replace("m", "").strip())
            except (ValueError, AttributeError):
                pass

        if has_gps:
            accuracy_note = f" (accuracy: {gps_accuracy}m)" if gps_accuracy else ""
            reasons.append(f"✓ GPS data present{accuracy_note}")
        else:
            reasons.append("⚠ No GPS data (indoor photo?)")

        # Check for HDR
        is_hdr = "HDR" in metadata.get("Apple:RunTimeFlags", "")
        if is_hdr:
            reasons.append("✓ HDR photo")

        # Check for Live Photo
        is_live_photo = metadata.get("Apple:ContentIdentifier", "").startswith("live")
        if is_live_photo:
            reasons.append("✓ Live Photo")

        # Extract date taken
        date_taken = (
            metadata.get("EXIF:DateTimeOriginal") or
            metadata.get("EXIF:CreateDate") or
            metadata.get("IFD0:DateTime")
        )

        # Final confidence (max 1.0)
        confidence_score = min(confidence_score, 1.0)

        # Decision: is_iphone_photo if confidence >= 0.7
        is_verified = confidence_score >= 0.7

        return iPhoneVerification(
            is_iphone_photo=is_verified,
            confidence=confidence_score,
            iphone_model=model,
            ios_version=ios_version,
            has_gps=has_gps,
            gps_latitude=gps_lat,
            gps_longitude=gps_lon,
            gps_accuracy=gps_accuracy,
            is_hdr=is_hdr,
            is_live_photo=is_live_photo,
            date_taken=date_taken,
            reasons=reasons
        )

    def _parse_gps(self, gps_str: Optional[str]) -> Optional[float]:
        """Parse GPS coordinate from EXIF format.

        Example: "47 deg 36' 22.32\" N" → 47.606200
        """
        if not gps_str:
            return None

        try:
            # Remove direction (N/S/E/W)
            gps_str = gps_str.split()[0] if " " in gps_str else gps_str

            # Handle different formats
            if "deg" in gps_str:
                # Format: "47 deg 36' 22.32\""
                parts = gps_str.replace("deg", "").replace("'", "").replace('"', "").split()
                degrees = float(parts[0])
                minutes = float(parts[1]) if len(parts) > 1 else 0
                seconds = float(parts[2]) if len(parts) > 2 else 0

                # Convert to decimal degrees
                return degrees + (minutes / 60.0) + (seconds / 3600.0)
            else:
                # Already decimal
                return float(gps_str)

        except (ValueError, IndexError):
            return None

    def batch_verify(self, photo_paths: list[Path]) -> list[Tuple[Path, iPhoneVerification]]:
        """Verify multiple photos efficiently."""
        results = []
        for photo_path in photo_paths:
            try:
                verification = self.verify_iphone_photo(photo_path)
                results.append((photo_path, verification))
            except Exception as e:
                print(f"Error verifying {photo_path}: {e}")

        return results


def main():
    """Test iPhone verification."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.metadata.iphone_verifier <photo_path>")
        sys.exit(1)

    photo_path = Path(sys.argv[1])

    verifier = iPhonePhotoVerifier()
    result = verifier.verify_iphone_photo(photo_path)

    print(f"\n{'='*60}")
    print(f"iPhone Photo Verification: {photo_path.name}")
    print(f"{'='*60}\n")

    print(f"Is iPhone Photo: {'✓ YES' if result.is_iphone_photo else '✗ NO'}")
    print(f"Confidence: {result.confidence:.1%}")

    if result.iphone_model:
        print(f"Model: {result.iphone_model}")
    if result.ios_version:
        print(f"iOS: {result.ios_version}")

    if result.has_gps:
        print(f"\nGPS: {result.gps_latitude:.6f}, {result.gps_longitude:.6f}")
        if result.gps_accuracy:
            print(f"GPS Accuracy: {result.gps_accuracy}m")
    else:
        print("\nGPS: Not available")

    if result.date_taken:
        print(f"Date Taken: {result.date_taken}")

    if result.is_hdr:
        print("HDR: Yes")
    if result.is_live_photo:
        print("Live Photo: Yes")

    print(f"\nVerification Details:")
    for reason in result.reasons:
        print(f"  {reason}")

    print()


if __name__ == "__main__":
    main()
