#!/bin/bash

# https://python-packaging-user-guide.readthedocs.io/tutorials/packaging-projects/

\rm -rf __pycache__ build dist scrapy_warcio.egg-info

python3 -m pip install --upgrade setuptools wheel
python3 -m pip install --upgrade twine

python3 setup.py sdist bdist_wheel

echo "---- PyPI ----"
echo "python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*"
echo "python3 -m twine upload dist/*"
