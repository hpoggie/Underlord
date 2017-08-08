#!/bin/bash
python setup.py build_apps
cd build
echo "cd \"\${0%/*}\";./Overlord" > manylinux1_x86_64/Overlord.sh
chmod +x manylinux1_x86_64/Overlord.sh
echo "setlocal;cd /d %~dp0;Overlord.exe" > win_amd64/Overlord.bat
zip -r manylinux1_x86_64 manylinux1_x86_64
zip -r win_amd64 win_amd64
