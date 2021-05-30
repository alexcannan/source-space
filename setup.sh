set -eufo pipefail

if [ ! -d env/ ]; then
    python3 -m venv env
    source env/bin/activate

    git clone https://github.com/alexcannan/newspaper.git

    cd newspaper/
    python -m pip install -r requirements.txt
    python setup.py install
    cd ..

    python -m pip install -r requirements.txt
    rm -rf newspaper
fi

source env/bin/activate