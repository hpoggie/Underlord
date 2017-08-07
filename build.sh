#!/bin/bash
pip freeze | grep panda3d > requirements.txt
python setup.py bdist_apps > build_output.txt
