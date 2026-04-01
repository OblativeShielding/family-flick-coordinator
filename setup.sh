#!/bin/bash
# written by ChatGPT
#
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

echo "Setup complete. Activate with: source .venv/bin/activate"