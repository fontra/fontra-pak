# Fontra Pak

Fontra Pak is a cross-platform, standalone, bundled [Fontra](https://github.com/fontra/fontra) application for desktop use.

## Download

Nightly builds can be downloaded from the topmost [“Build Application”](https://github.com/fontra/fontra-pak/actions) workflow. You need to be signed in to GitHub to be able to download.

## Run locally from source

To run the main program directly, set up a Python 3.10 (or higher) virtual environment, install the requirements from `requirements.txt`, then run:

    python FontraPakMain.py

## Build a self-contained application locally

To build a self-contained application, set up a Python 3.10 (or higher) virtual environment, install the requirements from `requirements.txt` and `requirements-dev.txt`, then run:

    pyinstaller FontraPak.spec -y

## How it works

Drop a font file onto application icon, or launch the application, and drop a font file onto the drop area. Or use the "New font" button to create a new font.

https://github.com/fontra/fontra-pak/assets/4246121/a4e8054e-995a-4bcc-ac64-5c8a0ea415aa
