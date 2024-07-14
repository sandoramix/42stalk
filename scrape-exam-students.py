import json
from api import API
from constants import JSON_EXAM_STUDENTS

PISCINE_EXAM = 18473

result = API.getExamExamsUsers(PISCINE_EXAM)

print(f"Loaded {len(result)} students")
with open(JSON_EXAM_STUDENTS, "w+") as file:
	json.dump(result, file, indent=2)
	print(f'at {JSON_EXAM_STUDENTS}')