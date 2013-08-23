#!/bin/bash
cd $(dirname $(readlink -f $0))
#PYLINT_FLAGS="--include-ids=yes "
PYLINT_FLAGS+="--errors-only " # disable all warnings, only report errors
PYLINT_FLAGS+="--enable=format " # enable formatting style checks
PYLINT_FLAGS+="--disable=C0301 " # disable line too long warnings
PYLINT_FLAGS+="--disable=C0302 " # disable module too long warnings
PYTHONPATH=src/python:tests:tests-1.3 pylint $PYLINT_FLAGS tests/*.py tests-1.3/*.py src/python/oftest/*.py
