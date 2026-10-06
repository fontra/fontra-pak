# Fontra Pak

Fontra Pak is a cross-platform, standalone, bundled [Fontra](https://github.com/fontra/fontra) application for desktop use.

## Download

Binaries for MacOS (11 and up), Windows (10 and up) and Ubuntu x86_64 can be [downloaded under releases](https://github.com/fontra/fontra-pak/releases/latest).

For Linux, there are more options, such as `flatpak` and `snap`: https://docs.fontra.xyz/how-tos/installation/installing-fontra-pak-linux/

## Run locally from source

To run the main program directly, set up a Python 3.11 (or higher) virtual environment, install the requirements from `requirements.txt`, then run:

    python FontraPakMain.py

## Native Linux installation

Fontra Pak can also be run directly from its Python environment on Linux.

This avoids the self-contained PyInstaller bundle and uses the libraries provided by the host system, including the host Qt, Wayland/X11, fontconfig and graphics stack.

To install for the current user:

    ./linux/install.sh

The default installation prefix is `~/.local`.

The launcher is installed as:

    ~/.local/bin/fontrapak

A desktop entry is also installed for the graphical desktop environment.

To uninstall:

    ./linux/uninstall.sh

## Build a self-contained application locally

To build a self-contained application, set up a Python 3.11 (or higher) virtual environment, install the requirements from `requirements.txt` and `requirements-dev.txt`, then run:

    pyinstaller FontraPak.spec -y

## How it works

Drop a font file onto application icon, or launch the application, and drop a font file onto the drop area or use the "Open File..." button to choose one. Or use the "New font..." button to create a new font.

https://github.com/fontra/fontra-pak/assets/4246121/a4e8054e-995a-4bcc-ac64-5c8a0ea415aa
