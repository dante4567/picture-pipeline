"""Tests for iPhone photo verification."""
import pytest
from pathlib import Path
from src.metadata.iphone_verifier import iPhonePhotoVerifier, iPhoneVerification


class TestiPhoneVerifier:
    """Test iPhone photo verification logic."""

    def test_verifier_initialization(self):
        """Test verifier can be initialized."""
        verifier = iPhonePhotoVerifier()
        assert verifier is not None

    def test_gps_parsing_dms(self):
        """Test GPS coordinate parsing (degrees/minutes/seconds)."""
        verifier = iPhonePhotoVerifier()

        # Test format: "47 deg 36' 22.32\""
        lat = verifier._parse_gps("47 deg 36' 22.32\"")
        assert lat is not None
        assert abs(lat - 47.606200) < 0.0001  # Tolerance for float comparison

    def test_gps_parsing_decimal(self):
        """Test GPS coordinate parsing (decimal)."""
        verifier = iPhonePhotoVerifier()

        lat = verifier._parse_gps("47.606200")
        assert lat == 47.606200

    def test_gps_parsing_invalid(self):
        """Test GPS parsing with invalid input."""
        verifier = iPhonePhotoVerifier()

        lat = verifier._parse_gps(None)
        assert lat is None

        lat = verifier._parse_gps("invalid")
        assert lat is None

    def test_verification_result_structure(self):
        """Test iPhoneVerification dataclass structure."""
        result = iPhoneVerification(
            is_iphone_photo=True,
            confidence=0.95,
            iphone_model="iPhone 14 Pro",
            ios_version="iOS 17.2",
            has_gps=True,
            gps_latitude=47.606200,
            gps_longitude=-122.332100,
            gps_accuracy=8.5,
            is_hdr=True,
            is_live_photo=False,
            date_taken="2024:06:15 10:23:45",
            reasons=["✓ Camera make: Apple", "✓ Camera model: iPhone 14 Pro"]
        )

        assert result.is_iphone_photo is True
        assert result.confidence == 0.95
        assert result.iphone_model == "iPhone 14 Pro"
        assert result.has_gps is True
        assert len(result.reasons) == 2


# Note: Full integration tests require actual iPhone photos
# Run with: ./run.sh verify-iphone /path/to/real/iphone/photo.jpg
