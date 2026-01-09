"""Configuration for picture-pipeline."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://raguser:ragpass@localhost:5432/ragdb"
)

# LiteLLM
LITELLM_URL = os.getenv("LITELLM_URL", "http://localhost:4000")

# Storage paths
STORAGE_BASE = Path(os.getenv("STORAGE_BASE", "~/.local/share/pictures")).expanduser()
NAS_BASE = Path(os.getenv("NAS_BASE", "/mnt/nas/photos")).expanduser()

# Storage structure
STORAGE = {
    "hot": {
        "thumbnails": STORAGE_BASE / "thumbs",
        "cache": STORAGE_BASE / "cache",
        "screenshots": STORAGE_BASE / "screenshots",
    },
    "warm": {
        "originals": NAS_BASE / "active",
        "sidecars": NAS_BASE / "active",
    },
    "cold": {
        "archive": NAS_BASE / "archive",
        "backups": NAS_BASE / "backups",
    }
}

# Thumbnail sizes
THUMBNAIL_SIZES = {
    "tiny": (150, 150),
    "small": (500, 500),
    "medium": (1920, 1080),
}

# Face recognition
FACE_RECOGNITION = {
    "confidence_threshold": 0.95,  # 95%+ for family
    "model": "hog",  # or 'cnn' for GPU
}

# iPhone verification
IPHONE_VERIFICATION = {
    "required_make": "Apple",
    "required_model_prefix": "iPhone",
    "required_tags": ["Apple:ContentIdentifier", "Apple:ImageUniqueID"],
}

# Storage path template
# Photos organized as: YYYY/YYYY-MM/pictures/ or YYYY/YYYY-MM/videos/
STORAGE_PATH_TEMPLATE = {
    "pictures": "{year}/{year}-{month:02d}/pictures/{filename}",
    "videos": "{year}/{year}-{month:02d}/videos/{filename}",
}

# File type classification
PICTURE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.raw', '.cr2', '.nef', '.arw', '.dng', '.gif', '.bmp', '.tiff', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.m4v', '.hevc', '.avi', '.mkv', '.webm', '.3gp'}

# Processing
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))

# Create directories
for tier in STORAGE.values():
    for path in tier.values():
        path.mkdir(parents=True, exist_ok=True)
