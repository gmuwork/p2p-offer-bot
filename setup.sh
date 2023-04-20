#!/bin/bash

set -euxo pipefail

python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip setuptools pip-tools pre-commit
pip install -r requirements.txt

pre-commit install
