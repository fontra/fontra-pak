# Fontra Pak

Fontra Pak is a cross-platform, standalone, bundled [Fontra](https://github.com/googlefonts/fontra) application for desktop use.

## Download

Nightly builds can be downloaded from the topmost [“Build Application”](https://github.com/googlefonts/fontra-pak/actions) workflow.
You need to be signed in to GitHub to be able to download.

## Build locally

In short, to build, set up a Python 3.10 (or higher) virtual environment, install the requirements from `requirements.txt`, then run:

    pyinstaller FontraPak.spec -y

In detail:

1. Download this repo using git:

    mkdir -p ~/src/github.com/googlefonts/ ;
    cd ~/src/github.com/googlefonts/ ;
    git clone --depth=1 https://github.com/googlefonts/fontra-pak.git ;

2. Enter the repo directory and create a [Python Virtual Environment](https://www.w3schools.com/python/python_virtualenv.asp)

    cd fontra-pak ;
    python3 -m venv venv ;

3. Install the python package requirements:

    pip install -r requirements.txt ;

4. Install the full GUI application package:

    pyinstaller FontraPak.spec -y ;

5. Run the application:

    ./dist/Fontra\ Pak ;

## How it works

Easy!

https://github.com/googlefonts/fontra-pak/assets/4246121/a4e8054e-995a-4bcc-ac64-5c8a0ea415aa
