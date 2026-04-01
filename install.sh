#!/bin/bash
# install.sh - Install swb for development

set -e

INSTALL_DIR="/usr/local/bin"
VENV_DIR="venv"

echo "Installing swb..."

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Install dependencies and package
echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install -q -r requirements.txt
"$VENV_DIR/bin/pip" install -q -e .

# Create wrapper script in /usr/local/bin
echo "Creating system-wide command..."
sudo tee "$INSTALL_DIR/swb" > /dev/null << EOF
#!/bin/bash
# swb wrapper script
exec "$PWD/$VENV_DIR/bin/swb" "\$@"
EOF

sudo chmod +x "$INSTALL_DIR/swb"

echo ""
echo "Installation complete!"
echo "Run 'swb --help' to get started."
