#!/bin/bash

if [ ! -d env/ ]; then
    python3 -m venv env
    source env/bin/activate

    git clone https://github.com/alexcannan/newspaper.git
    cd newspaper/
    python -m pip install -r requirements.txt
    python setup.py install
    cd ..
    rm -rf newspaper

    python -m pip install -e .
fi

source env/bin/activate