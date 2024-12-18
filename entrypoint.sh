#!/bin/bash

set -e

PYTHONVERSION=3.10

if [ -n "$2" ]; then

    PYTHONVERSION="$2"
    echo "updating python version to $PYTHONVERSION"
    pyenv install -s $PYTHONVERSION
    pyenv global $PYTHONVERSION
    pip install -r requirements.txt
    echo "python version updated to $PYTHONVERSION"
fi

python src/main.py $1