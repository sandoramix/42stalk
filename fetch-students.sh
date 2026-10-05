#!/bin/bash
# Usage: ./fetch-students.sh [campus_id]
# Saves the students of a campus to data/campus_<campus_id>_students.json
cd "$(dirname "$0")"
./pyenv/bin/python fetch-students.py "$@"
