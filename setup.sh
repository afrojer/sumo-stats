#!/bin/zsh

if [ -d .venv ]; then
	echo "source .venv/bin/activate"
	exit 0
fi

python3 -m venv .venv
source .venv/bin/activate
chmod 755 .venv/bin/activate
pip3 install httpx
pip3 install dataclasses_json
