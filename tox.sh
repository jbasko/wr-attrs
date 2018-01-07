#!/bin/bash

# This script runs tox with Python 3.6 and Python 3.5 with pyenv managed virtualenvs.

set +e

original_pyenv=$PYENV_VERSION

# Test with Python 3.6
export PYENV_VERSION=wr-attrs-36

tox -e py36

# Test with Python 3.5

export PYENV_VERSION=wr-attrs-35
tox -e py35


# Set back to current Python
export PYENV_VERSION=${original_pyenv}
