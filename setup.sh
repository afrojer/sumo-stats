#!/bin/zsh

[ -d .venv ] && exit 0

python3 -m venv .venv
source ./venv/bin/activate
pip3 install httpx
pip3 install dataclasses_json
