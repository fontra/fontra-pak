#!/usr/bin/env bash
set -euo pipefail

APP_ID="xyz.fontra.FontraPak"

PREFIX="${PREFIX:-$HOME/.local}"
APP_DIR="${PREFIX}/lib/fontrapak"
BIN_DIR="${PREFIX}/bin"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

echo "==> Removing Fontra Pak"

rm -rf "${APP_DIR}"
rm -f "${BIN_DIR}/fontrapak"
rm -f "${DESKTOP_DIR}/${APP_ID}.desktop"
rm -f "${ICON_DIR}/${APP_ID}.svg"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" || true
fi

echo "Fontra Pak has been removed."
