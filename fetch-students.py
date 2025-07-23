import json
from api import API, CONFIG, CONSTANTS, selectCampus
from constants import JSON_STUDENTS
import os
import sys

requestedCampusId = sys.argv[1] if len(sys.argv) > 1 else None
if requestedCampusId is not None and requestedCampusId.isdigit():
	selectCampus(int(requestedCampusId))

result = API.getCampusUsers(CONFIG[CONSTANTS['DEFAULT_CAMPUS']])

print(f"Loaded {len(result)} students")
output_path = JSON_STUDENTS(CONFIG[CONSTANTS["DEFAULT_CAMPUS"]])
with open(output_path, "w+") as file:
	json.dump(result, file, indent=2)
	print(f'at {output_path}')