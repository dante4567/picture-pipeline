#!/usr/bin/env bash
# Picture Pipeline entry point

set -e

case "$1" in
    verify-iphone)
        if [ -z "$2" ]; then
            echo "Usage: ./run.sh verify-iphone <photo_path>"
            exit 1
        fi
        echo "Verifying iPhone photo: $2"
        python -m src.metadata.iphone_verifier "$2"
        ;;

    test)
        echo "Running tests..."
        pytest tests/ -v
        ;;

    setup)
        echo "Setting up picture-pipeline..."
        echo "1. Installing Python dependencies..."
        pip install -r requirements.txt

        echo "2. Checking ExifTool..."
        if ! command -v exiftool &> /dev/null; then
            echo "⚠️  ExifTool not found!"
            echo "Install: sudo apt install libimage-exiftool-perl"
            exit 1
        else
            echo "✓ ExifTool found: $(exiftool -ver)"
        fi

        echo "3. Creating storage directories..."
        python -c "import src.config"

        echo ""
        echo "✅ Setup complete!"
        echo ""
        echo "Next steps:"
        echo "  1. Test iPhone verification: ./run.sh verify-iphone /path/to/iphone/photo.jpg"
        echo "  2. Run tests: ./run.sh test"
        ;;

    inventory)
        echo "Running photo source inventory..."
        python -m src.ingestion.inventory
        ;;

    import)
        echo "Import not yet implemented"
        echo "Coming soon: Import photos from directory"
        ;;

    *)
        echo "Picture Pipeline - Centralized photo management"
        echo ""
        echo "Usage: ./run.sh {command}"
        echo ""
        echo "Commands:"
        echo "  setup              Set up picture-pipeline (install deps, check exiftool)"
        echo "  inventory          Scan all photo sources and generate inventory report"
        echo "  verify-iphone      Verify if photo is from iPhone"
        echo "  test               Run tests"
        echo "  import             Import photos (not yet implemented)"
        echo ""
        echo "Examples:"
        echo "  ./run.sh setup"
        echo "  ./run.sh verify-iphone ~/Pictures/IMG_1234.jpg"
        exit 1
        ;;
esac
