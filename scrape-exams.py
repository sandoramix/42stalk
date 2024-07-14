import json
from api import API
from constants import CAMPUS_ID_42FIRENZE, JSON_EXAMS


result = API.getCampusExams(CAMPUS_ID_42FIRENZE)

print(f"Loaded {len(result)} exams")
with open(JSON_EXAMS, "w+") as file:
	json.dump(result, file, indent=2)
	print(f'at {JSON_EXAMS}')