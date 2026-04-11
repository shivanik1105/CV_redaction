#!/bin/bash
# Bash script to test CV redaction
# Usage: ./test_cv_redaction.sh <path_to_pdf>

if [ $# -eq 0 ]; then
    echo "Usage: $0 <path_to_pdf>"
    exit 1
fi

PDF_PATH="$1"

if [ ! -f "$PDF_PATH" ]; then
    echo "Error: File not found: $PDF_PATH"
    exit 1
fi

echo "Testing CV Redaction..."
echo "Input: $PDF_PATH"
echo ""

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the test
python app_launcher.py --test "$PDF_PATH"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "Test completed successfully!"
else
    echo ""
    echo "Test failed!"
fi

exit $exit_code
