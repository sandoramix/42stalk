from os import path, mkdir

CAMPUS_ID_42FIRENZE = 52


OUT_DIR = path.abspath("data")

if not path.exists(OUT_DIR):
	mkdir(OUT_DIR)

JSON_CONFIG = path.join("config.json")
# ---------- JSON NAMES ------------
JSON_CAMPUSES = path.join(OUT_DIR, "campuses.json")

JSON_STUDENTS = lambda campus: path.join(OUT_DIR, f"campus_{campus}_students.json")
JSON_PISCINE = path.join(OUT_DIR, "piscine.json")
JSON_EXAMS = path.join(OUT_DIR, "exams.json")
JSON_EXAM_STUDENTS = path.join(OUT_DIR, "exam_students.json")