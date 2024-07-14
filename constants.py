from os import path

CAMPUS_ID_42FIRENZE = 52


OUT_DIR = path.abspath("data")

# ---------- JSON NAMES ------------
JSON_STUDENTS = path.join(OUT_DIR, "students.json")
JSON_PISCINE = path.join(OUT_DIR, "piscine.json")
JSON_EXAMS = path.join(OUT_DIR, "exams.json")
JSON_EXAM_STUDENTS = path.join(OUT_DIR, "exam_students.json")