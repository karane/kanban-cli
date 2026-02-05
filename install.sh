#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.local/share/kanban-cli"
BIN_DIR="$HOME/.local/bin"

echo "Creating virtual environment..."
python3 -m venv "$INSTALL_DIR"

echo "Installing kanban-cli..."
"$INSTALL_DIR/bin/pip" install "$SCRIPT_DIR"

mkdir -p "$BIN_DIR"
ln -sf "$INSTALL_DIR/bin/kbcli" "$BIN_DIR/kbcli"

echo ""
echo "Installed! Run 'kbcli' to get started."
echo "(Make sure ~/.local/bin is on your PATH)"
