#!/bin/bash
# Installation script for Hanzo ACI

echo "Installing Hanzo ACI..."

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed. Please install pip first."
    exit 1
fi

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: It's recommended to install Hanzo ACI in a virtual environment."
    echo "You can create a virtual environment with:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    
    # Ask if the user wants to continue
    read -p "Do you want to continue with the installation? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation aborted."
        exit 0
    fi
fi

# Install the package
echo "Installing package..."
pip install -e ".[dev,all]"

echo "Installation complete!"
echo "You can now use Hanzo ACI by running:"
echo "  python -m hanzo_aci.cli"
echo "Or:"
echo "  hanzo-aci"
