#!/usr/bin/env bash
set -e

INSTALL_DIR="$HOME/.local/share/kanban-cli"
BIN_DIR="$HOME/.local/bin"

rm -f "$BIN_DIR/kbcli"
rm -rf "$INSTALL_DIR"

echo ""
echo "Uninstalled."
