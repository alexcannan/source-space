from setuptools import setup, find_namespace_packages

setup(
    name='articlesa',
    version='0',
    python_requires='>=3.8',
    author='Alex Cannan',
    author_email='alexfcannan@gmail.com',
    packages=find_namespace_packages(include=['articlesa.*']),
    long_description="article source aggregator generates source maps for online articles",
    install_requires=open("requirements.txt").read().split("\n")
)

