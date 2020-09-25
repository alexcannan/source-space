git clone https://github.com/alexcannan/newspaper.git

cd newspaper/
python -m pip install -r requirements.txt
python setup.py install
cd ..

python -m pip install -r requirements.txt
rm -rf newspaper