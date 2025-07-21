import json
import logging
import os
from flask import Flask, render_template, request, send_from_directory
import time
from collections import defaultdict
import numbers
import re

from api import API

SERVER_PORT = 8080

USER_CACHE_DIR = "../data/"
if (not os.path.exists(USER_CACHE_DIR)):
	os.mkdir(USER_CACHE_DIR)
USER_CACHE_PATH = os.path.join(USER_CACHE_DIR, "cached_users.json")
CACHE_EXPIRATION_DAYS = 2

# Only these are filtered BEFORE fullscan
BASIC_FILTERS = {
	"id", "email", "login", "first_name", "last_name", "usual_full_name",
	"usual_first_name", "url", "phone", "displayname", "kind",
	"correction_point", "pool_month", "pool_year", "location",
	"wallet", "anonymize_date", "data_erasure_date", "created_at",
	"updated_at", "alumnized_at", "alumni", "active", "staff"
}

CUSTOM_FILTERS = [
	{"name": "fullscan", "type": "boolean", "nullable": True},
	{"name": "examname", "type": "string", "nullable": True},
	{"name": "projectname", "type": "string", "nullable": True}
]

cachedUsers = []


app = Flask("server")

@app.route("/api/students")
def StudentsAPI():
	try:
		with open("../data/students.json", 'r') as file:
			return json.load(file)
	except Exception as e:
		logging.exception(e)
		exit(1)
		return []

@app.route("/api/students/keys")
def StudentsKeysAPI(customData=None):
	if customData:
		students = customData
	else:
		students = StudentsAPI()
	if not students or len(students) == 0:
		return []

	field_types = defaultdict(set)
	field_nullable = defaultdict(lambda: False)

	for student in students:
		flat = flatten_keys(student)
		for key, typ in flat.items():
			if typ == "null":
				field_nullable[key] = True
			else:
				field_types[key].add(typ)
		# Mark missing keys as nullable
		seen_keys = set(flat.keys())
		all_keys_so_far = set(field_types.keys())
		for key in all_keys_so_far - seen_keys:
			field_nullable[key] = True

	result = []
	for key in sorted(field_types.keys()):
		types = sorted(field_types[key])
		result.append({
			"name": key,
			"type": types[0] if len(types) == 1 else "|".join(types),
			"nullable": field_nullable[key]
		})

	result.extend(CUSTOM_FILTERS)

	return result


#------------------------------------------------------------------------------
# JSON KEYS RETRIEVAL


def infer_type(value):
	if isinstance(value, bool):
		return "boolean"
	elif isinstance(value, numbers.Number):
		return "number"
	elif isinstance(value, dict):
		return "object"
	elif isinstance(value, list):
		return "array"
	elif value is None:
		return "null"
	else:
		return "string"

def flatten_keys(obj, parent_key=""):
	items = {}
	if isinstance(obj, dict):
		for k, v in obj.items():
			new_key = f"{parent_key}.{k}" if parent_key else k
			if isinstance(v, dict):
				items.update(flatten_keys(v, new_key))
			elif isinstance(v, list):
				# If list, flatten first non-null item
				if v:
					# Try multiple entries to get consistent shape
					for i in v:
						if isinstance(i, dict):
							items.update(flatten_keys(i, new_key))
							break
					else:
						items[new_key] = infer_type(v)
				else:
					items[new_key] = "array"
			else:
				items[new_key] = infer_type(v)
	else:
		items[parent_key] = infer_type(obj)
	return items

#------------------------------------------------------------------------------
# FETCH STUDENT DATA

def getStudData(user, idx = -1):
	_ = API.getUserByID(user["id"])
	if (not _):
		_ = user
		_['failedFetchExams'] = True
	else:
		_['failedFetchExams'] = False
		_['all_projects'] = _['projects_users']
		_['exams'] = [i for i in _['projects_users'] if 'project' in i and 'slug' in i['project'] and 'exam' in i['project']['slug'].lower()]
		_['projects'] = [i for i in _['projects_users'] if 'project' in i and 'slug' in i['project'] and 'exam' not in i['project']['slug'].lower()]
	print(f'parsed-[{idx}]\t{user["id"]=}\t{user["login"]=}\t{len(_["all_projects"])=}')
	return _

#-------------------------------------------------------------------------------
# CACHING FUNCTIONS

def load_user_cache():
	if not os.path.exists(USER_CACHE_PATH):
		return {}
	try:
		with open(USER_CACHE_PATH, 'r') as f:
			return json.load(f)
	except Exception as e:
		logging.exception(f"Failed to load user cache: {e}")
		return {}

def save_user_cache(cache):
	try:
		with open(USER_CACHE_PATH, 'w') as f:
			json.dump(cache, f, indent=2)
	except Exception as e:
		logging.exception(f"Failed to save user cache: {e}")

def is_cache_expired(timestamp_str):
	try:
		last_saved = float(timestamp_str)
		age_days = (time.time() - last_saved) / (60 * 60 * 24)
		return age_days > CACHE_EXPIRATION_DAYS
	except:
		return True

def invalidateCache(filteredList: "list"=[]):

	global cachedUsers
	cache = load_user_cache()
	cachedUsers = cache

	result = []

	for idx, user in enumerate(filteredList):
		user_id = str(user['id'])
		cache_entry = cache.get(user_id)

		# Needs fetch if not cached or expired
		if not cache_entry or is_cache_expired(cache_entry.get('lastSave')):
			fetched_user = getStudData(user, idx)
			fetched_user['lastSave'] = str(time.time())
			cache[user_id] = fetched_user
			result.append(fetched_user)
		else:
			result.append(cache_entry)

	save_user_cache(cache)
	print(f'Cache invalidated. New size: {len(result)}')
	return result

#-------------------------------------------------------------------------------


def nested(obj, attr_path, first=False, flatten=True, as_set=False):
	parts = attr_path.split(".")

	def parse_key(part):
		"""Handles list indices like 'key[0]' or just 'key'"""
		match = re.match(r"(\w+)(?:\[(\d+)\])?", part)
		if not match:
			return part, None
		key, idx = match.groups()
		return key, int(idx) if idx is not None else None

	def _extract(current, keys):
		if not keys:
			return current

		key_part = keys[0]
		rest = keys[1:]
		key, idx = parse_key(key_part)

		if isinstance(current, dict):
			if key not in current:
				return None
			next_item = current[key]
			if idx is not None:
				if isinstance(next_item, list) and 0 <= idx < len(next_item):
					return _extract(next_item[idx], rest)
				return None
			return _extract(next_item, rest)

		elif isinstance(current, list):
			results = [_extract(item, keys) for item in current]
			if flatten:
				flattened = []
				for r in results:
					if isinstance(r, list):
						flattened.extend(r)
					elif r is not None:
						flattened.append(r)
				return flattened if flattened else None
			else:
				return results

		return None

	result = _extract(obj, parts)

	if first:
		if isinstance(result, list):
			return result[0] if result else None
	if as_set and isinstance(result, list):
		return list(set(result))
	return result


def conditional(value, condition):
	condition = str(condition)
	if condition.startswith(">="):
		return str(value) >= str(condition[2:])
	elif condition.startswith("<="):
		return str(value) <= str(condition[2:])
	elif condition.startswith(">"):
		return str(value) > str(condition[1:])
	elif condition.startswith("<"):
		return str(value) < str(condition[1:])
	elif condition.startswith("=="):
		return str(value) == str(condition[2:])
	elif condition.startswith("!="):
		return str(value) != str(condition[2:])
	else:
		return str(condition) in str(value)


def get_first_exam_final_mark(projects: list):
	# Use .get() to provide a default empty list if 'projects_users' key is missing
	exams = [p for p in projects if p['final_mark'] is not None]
	return exams[0]['final_mark'] if exams else None

def sort_by_exam_final_grade_and_login(users: "list[dict]"):
	return sorted(users, key=lambda user: user['average_exam_final_mark'], reverse=True)

def get_average_final_mark(user, objName="exams"):
	exams = user.get(objName, [])
	total = sum([e['final_mark'] for e in exams if e['final_mark'] is not None or 0])
	if len(exams) == 0:
		return 0
	return total / len(exams)


@app.route("/")
def Homepage():
	students = StudentsAPI()
	if len(students) == 0:
		return render_template("index.html", students=[], fields=[])

	args = request.args

	checkForFinalExam = args.get("fullscan") is not None
	examNameFilter = args.get("examname", "").lower()
	projectNameFilter = args.get("projectname", "").lower()

	# -----------------------------
	# 1. BASIC FILTERS — pre-fetch
	# -----------------------------
	filtered = students
	for arg, val in args.items():
		arg_lower = arg.lower()
		if arg in BASIC_FILTERS:
			filtered = [
				stud for stud in filtered
				if conditional(nested(stud, arg_lower, as_set=True), val)
			]

	# ---------------------------------
	# 2. Fullscan if requested (fetch)
	# ---------------------------------
	if checkForFinalExam:
		filtered = invalidateCache(filteredList=filtered)

		# -----------------------------
		# 3. CUSTOM FILTERS — post-fetch
		# -----------------------------
		for arg, val in args.items():
			arg_lower = arg.lower()
			if arg in BASIC_FILTERS or [i['name'] for i in CUSTOM_FILTERS if i['name'] == arg_lower]:
				continue  # already applied or internal
			filtered = [
				stud for stud in filtered
				if conditional(nested(stud, arg_lower, as_set=True), val)
			]

	# -------------------------
	# Final processing
	# -------------------------
	for user in filtered:
		user['exams'] = [e for e in user.get('all_projects', []) if 'exam' in e['project']['slug'].lower() and (examNameFilter in e['project']['slug'].lower() or examNameFilter == '')]
		user['projects'] = [e for e in user.get('all_projects', []) if 'exam' not in e['project']['slug'].lower() and (projectNameFilter in e['project']['slug'].lower() or projectNameFilter == '')]
		user['average_exam_final_mark'] = get_average_final_mark(user)
		user['average_project_final_mark'] = get_average_final_mark(user, objName="projects")
		user['average_mark'] = get_average_final_mark(user, objName="all_projects")

	sorted_result = sort_by_exam_final_grade_and_login(filtered)

	fields = StudentsKeysAPI(customData=sorted_result)
	return render_template("index.html", students=sorted_result, students_json=json.dumps(sorted_result), fields=fields)

#-------------------------------------------------------------------------------

@app.route('/favicon.ico')
def favicon():
	return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/static/<file>')
def static_files(file):
	return send_from_directory(os.path.join(app.root_path, 'static'), file)

@app.route("/<page>")
def Other(page):
	return render_template(f"{page}.html")

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=SERVER_PORT)