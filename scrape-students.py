import json
from api import API
from constants import CAMPUS_ID_42FIRENZE, JSON_STUDENTS


result = API.getCampusUsers(CAMPUS_ID_42FIRENZE)

print(f"Loaded {len(result)} students")
with open(JSON_STUDENTS, "w+") as file:
	json.dump(result, file, indent=2)
	print(f'at {JSON_STUDENTS}')