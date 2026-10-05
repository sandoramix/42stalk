import json
from api import API, CONFIG, CONSTANTS, selectCampus
from constants import JSON_STUDENTS
import os
import sys

requestedCampusId = sys.argv[1] if len(sys.argv) > 1 else None
if requestedCampusId is not None and requestedCampusId.isdigit():
	selectCampus(int(requestedCampusId))

result = API.getCampusUsers(CONFIG[CONSTANTS['DEFAULT_CAMPUS']])

campus_id = CONFIG[CONSTANTS["DEFAULT_CAMPUS"]]
print(f"Loaded {len(result)} students")
output_path = JSON_STUDENTS(campus_id)
with open(output_path, "w+") as file:
	json.dump(result, file, indent=2)
	print(f'Saved to {output_path}')

print(f"""
Next steps:
  1. Start the web app:   ./run-server.sh
  2. Open:                http://localhost:8080/?campus_id={campus_id}

Without ?campus_id the app reads data/students.json if it exists, otherwise the
default campus from config.json (currently {campus_id}). You can switch between
fetched campuses from the selector at the top of the page, and fetch or update
campuses from the web app too (cloud button next to the selector).
Exams and projects are loaded on demand with "Full scan" (one 42 API request per
student the first time, then cached for 12h in data/cached_users.json).""")