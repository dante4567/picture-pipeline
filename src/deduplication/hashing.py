"""Photo hashing for identity and visual similarity.

SHA256: File identity, provenance, integrity ("which file is this?")
pHash: Visual similarity ("is this the same photo visually?")
"""

import hashlib
import imagehash
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import logging

# Register HEIF/HEIC support for Pillow
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # pillow-heif not installed, HEIC support unavailable

logger = logging.getLogger(__name__)


@dataclass
class PhotoHashes:
    """Hash results for a photo."""
    sha256: str  # File identity (entire file bytes)
    phash: str   # Perceptual hash (visual content only)
    file_size: int
    error: Optional[str] = None


def calculate_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """Calculate SHA256 hash of file (raw bytes).

    Args:
        file_path: Path to file
        chunk_size: Read chunk size (default 8KB for efficiency)

    Returns:
        SHA256 hash as hex string (64 characters)
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def calculate_phash(file_path: Path, hash_size: int = 16) -> str:
    """Calculate perceptual hash (visual similarity).

    Uses difference hash (dHash) algorithm:
    - Resizes image to hash_size+1 x hash_size
    - Converts to grayscale
    - Compares adjacent pixels (left vs right)
    - Generates binary hash from differences

    Args:
        file_path: Path to image file
        hash_size: Hash size (default 16 = 256-bit hash)

    Returns:
        Perceptual hash as hex string

    Raises:
        ValueError: If file cannot be opened as image
    """
    try:
        with Image.open(file_path) as img:
            # Use dHash (difference hash) - faster than pHash, similar accuracy
            phash = imagehash.dhash(img, hash_size=hash_size)
            return str(phash)
    except Exception as e:
        raise ValueError(f"Cannot calculate phash: {e}")


def hash_photo(file_path: Path) -> PhotoHashes:
    """Calculate both SHA256 and pHash for a photo.

    Args:
        file_path: Path to photo file

    Returns:
        PhotoHashes with both hashes, or error if failed
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return PhotoHashes(
            sha256="",
            phash="",
            file_size=0,
            error=f"File not found: {file_path}"
        )

    file_size = file_path.stat().st_size

    # Calculate SHA256 (always succeeds for readable files)
    try:
        sha256 = calculate_sha256(file_path)
    except Exception as e:
        return PhotoHashes(
            sha256="",
            phash="",
            file_size=file_size,
            error=f"Cannot read file: {e}"
        )

    # Calculate pHash (may fail for non-image files)
    try:
        phash = calculate_phash(file_path)
    except Exception as e:
        logger.warning(f"Cannot calculate phash for {file_path}: {e}")
        # Still return SHA256 (file identity works even if visual hash fails)
        return PhotoHashes(
            sha256=sha256,
            phash="",
            file_size=file_size,
            error=f"Cannot calculate phash: {e}"
        )

    return PhotoHashes(
        sha256=sha256,
        phash=phash,
        file_size=file_size
    )


def compare_phashes(phash1: str, phash2: str) -> int:
    """Compare two perceptual hashes (Hamming distance).

    Args:
        phash1: First perceptual hash (hex string)
        phash2: Second perceptual hash (hex string)

    Returns:
        Hamming distance (0 = identical, higher = more different)
        Typical thresholds:
        - 0-5: Very similar (likely same photo, different metadata)
        - 6-15: Similar (possibly cropped/edited version)
        - 16+: Different photos
    """
    # Convert hex strings back to imagehash.ImageHash objects
    hash1 = imagehash.hex_to_hash(phash1)
    hash2 = imagehash.hex_to_hash(phash2)

    # Calculate Hamming distance
    return hash1 - hash2


def find_similar_photos(
    target_phash: str,
    candidate_phashes: dict[str, str],
    threshold: int = 5
) -> list[Tuple[str, int]]:
    """Find visually similar photos using perceptual hash.

    Args:
        target_phash: Perceptual hash to search for
        candidate_phashes: Dict of {file_id: phash} to search in
        threshold: Max Hamming distance (default 5 = very similar)

    Returns:
        List of (file_id, distance) sorted by similarity (closest first)
    """
    target_hash = imagehash.hex_to_hash(target_phash)

    similar = []
    for file_id, phash in candidate_phashes.items():
        candidate_hash = imagehash.hex_to_hash(phash)
        distance = target_hash - candidate_hash

        if distance <= threshold:
            similar.append((file_id, distance))

    # Sort by distance (most similar first)
    similar.sort(key=lambda x: x[1])

    return similar


def batch_hash_photos(file_paths: list[Path], progress_callback=None) -> dict[Path, PhotoHashes]:
    """Hash multiple photos with optional progress reporting.

    Args:
        file_paths: List of photo paths to hash
        progress_callback: Optional callback(current, total, file_path)

    Returns:
        Dict of {file_path: PhotoHashes}
    """
    results = {}
    total = len(file_paths)

    for idx, file_path in enumerate(file_paths, 1):
        hashes = hash_photo(file_path)
        results[file_path] = hashes

        if progress_callback:
            progress_callback(idx, total, file_path)

        # Log errors
        if hashes.error:
            logger.error(f"Error hashing {file_path}: {hashes.error}")

    return results


if __name__ == "__main__":
    # Test with sample photos
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.deduplication.hashing <photo1> [photo2]")
        sys.exit(1)

    # Hash first photo
    photo1 = Path(sys.argv[1])
    print(f"Hashing: {photo1}")
    hashes1 = hash_photo(photo1)

    if hashes1.error:
        print(f"❌ Error: {hashes1.error}")
    else:
        print(f"✅ SHA256: {hashes1.sha256}")
        print(f"✅ pHash:  {hashes1.phash}")
        print(f"   Size:   {hashes1.file_size:,} bytes")

    # Compare with second photo if provided
    if len(sys.argv) >= 3:
        photo2 = Path(sys.argv[2])
        print(f"\nHashing: {photo2}")
        hashes2 = hash_photo(photo2)

        if hashes2.error:
            print(f"❌ Error: {hashes2.error}")
        else:
            print(f"✅ SHA256: {hashes2.sha256}")
            print(f"✅ pHash:  {hashes2.phash}")
            print(f"   Size:   {hashes2.file_size:,} bytes")

            # Compare
            if hashes1.phash and hashes2.phash:
                distance = compare_phashes(hashes1.phash, hashes2.phash)
                print(f"\n🔍 Visual similarity:")
                print(f"   Hamming distance: {distance}")
                if distance == 0:
                    print("   → Identical visual content")
                elif distance <= 5:
                    print("   → Very similar (likely same photo, different metadata)")
                elif distance <= 15:
                    print("   → Similar (possibly cropped/edited)")
                else:
                    print("   → Different photos")

                # SHA256 comparison
                if hashes1.sha256 == hashes2.sha256:
                    print(f"\n🔍 File identity: IDENTICAL (same file)")
                else:
                    print(f"\n🔍 File identity: DIFFERENT (different files)")
