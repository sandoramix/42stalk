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
# keep the students fetched before that the 42 API no longer returns
fetched_ids = {u.get("id") for u in result}
kept = []
if os.path.exists(output_path):
	try:
		with open(output_path, "r") as file:
			kept = [u for u in json.load(file) if u.get("id") not in fetched_ids]
	except Exception as e:
		print(f"Couldn't read the previous {output_path}: {e}")
with open(output_path, "w+") as file:
	json.dump(result + kept, file, indent=2)
	print(f'Saved to {output_path}' + (f' ({len(kept)} older students kept)' if kept else ''))

print(f"""
Next steps:
  1. Start the web app:   ./run-server.sh
  2. Open:                http://localhost:8080/?campus_id={campus_id}

Without ?campus_id the app reads data/students.json if it exists, otherwise the
default campus from config.json (currently {campus_id}). You can switch between
fetched campuses from the selector at the top of the page, and fetch or update
campuses from the web app too (cloud button next to the selector).
Exams and projects are loaded on demand with "Full scan" (one 42 API request per
student the first time, then kept in data/cached_users.json; "Rescan" updates the
profiles older than 12h).""")