#!/usr/bin/env bash
set -euo pipefail

APP_ID="xyz.fontra.FontraPak.Native"
APP_NAME="Fontra Pak"

PREFIX="${PREFIX:-$HOME/.local}"
APP_DIR="${PREFIX}/lib/fontrapak"
BIN_DIR="${PREFIX}/bin"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

PYTHON="${PYTHON:-python3}"

echo "==> Installing ${APP_NAME}"
echo "    Source: ${PROJECT_DIR}"
echo "    Prefix: ${PREFIX}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "error: python3 is required" >&2
    exit 1
fi

PYTHON_VERSION="$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

if ! "$PYTHON" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
    echo "error: Python 3.11 or newer is required (found ${PYTHON_VERSION})" >&2
    exit 1
fi

mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"

if [[ ! -d "${APP_DIR}/venv" ]]; then
    echo "==> Creating virtual environment"
    "$PYTHON" -m venv "${APP_DIR}/venv"
fi

VENV="${APP_DIR}/venv"

echo "==> Updating packaging tools"
"${VENV}/bin/python" -m pip install --upgrade pip

echo "==> Installing Fontra Pak dependencies"
"${VENV}/bin/python" -m pip install -r "${PROJECT_DIR}/requirements.txt"

echo "==> Installing Fontra Pak"

# Keep the source tree as the application source for now.
# This avoids PyInstaller and therefore uses the host Linux libraries.
ln -sfn "${PROJECT_DIR}/FontraPakMain.py" "${APP_DIR}/FontraPakMain.py"

cat > "${BIN_DIR}/fontrapak" <<EOF
#!/usr/bin/env bash
exec "${VENV}/bin/python" "${APP_DIR}/FontraPakMain.py" "\$@"
EOF

chmod +x "${BIN_DIR}/fontrapak"

echo "==> Installing desktop entry"

cat > "${DESKTOP_DIR}/${APP_ID}.desktop" <<EOF
[Desktop Entry]
Name=${APP_NAME} (Native)
Comment=Font editor and design application
Exec=${BIN_DIR}/fontrapak %F
Icon=${APP_ID}
Terminal=false
Type=Application
Categories=Graphics;Development;
MimeType=
StartupNotify=true
StartupWMClass=fontrapak
EOF

echo "==> Installing icon"

if [[ -f "${PROJECT_DIR}/icon/FontraIcon.svg" ]]; then
    install -m 0644 \
        "${PROJECT_DIR}/icon/FontraIcon.svg" \
        "${ICON_DIR}/${APP_ID}.svg"
else
    echo "warning: icon/FontraIcon.svg not found; desktop entry installed without an icon file"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" || true
fi

echo
echo "Installation complete."
echo
echo "Run:"
echo "  ${BIN_DIR}/fontrapak"
echo
echo "If ${BIN_DIR} is not in PATH:"
echo "  export PATH=\"${BIN_DIR}:\$PATH\""
