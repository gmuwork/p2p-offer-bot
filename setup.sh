#!/bin/bash

set -euo pipefail

if [ -d "venv" ]; then
  if [ "$#" -gt 0 ] && [ "$1" == "--force" ]; then
    echo "Removing existing environment from './venv/'"
    rm -rf ./venv
  else
    echo "Environment already exists, remove it with 'rm -rf ./venv/' or use '--force'"
    exit 1
  fi
fi

echo "Creating a new env in './venv/'"

python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip setuptools pip-tools pre-commit

echo "Installing dependencies"
pip install -r requirements.txt


echo "Setting up pre-commits"
pre-commit install

echo "Done."
