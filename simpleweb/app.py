import json
import logging
import os
from flask import Flask, render_template, request, send_from_directory
import time

from api import API

SERVER_PORT = 8080

app = Flask("server")

@app.route("/api/students")
def StudentsAPI():
	try:
		with open("../data/students.json", 'r') as file:
			return json.load(file)
	except Exception as e:
		logging.exception(e)
		return None

#-------------------------------------------------------------------------------

def nested(obj, attr_path):
	attrs = attr_path.split('.')
	current_obj = obj
	try:
		for attr in attrs:
			current_obj = current_obj[attr]
		return current_obj
	except Exception:
		return None

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

lastRefresh = 0
refreshSeconds = 300
cachedUsers = []

def getStudData(user, idx = -1):
	result = API.getUserByID(user["id"])
	if (not result):
		result = user
		result['failedFetchExams'] = True
	else:
		result['fetchExams'] = True
		result['currentExams'] = [i for i in result['projects_users'] if 'project' in i and 'slug' in i['project'] and 'exam' in i['project']['slug'].lower()]
	print(f'parsed-[{idx}]\t{user["id"]=}\t{len(result["currentExams"])=}')
	return result

def invalidateCache(filteredList=None):
	global cachedUsers
	global lastRefresh

	print(f'pre-cached-{len(cachedUsers)=}')
	cachedIdxs = [i['id'] for i in cachedUsers]
	requestedIdxs = [i['id'] for i in filteredList]
	result = filteredList
	cachedForFirstTime = [i for i in result if i['id'] not in cachedIdxs]

	for idx, reqUser in enumerate(result):
		if reqUser['id'] not in cachedIdxs:
			newCache = getStudData(reqUser, idx)
			cachedUsers.append(newCache)
			result[idx] = newCache
		else:
			result[idx] = cachedUsers[cachedIdxs.index(reqUser['id'])]
	print(f'lastRefresh-{lastRefresh=}\t{time.time()=} refreshAt-{lastRefresh + refreshSeconds=}')
	if lastRefresh == 0 or lastRefresh + refreshSeconds > time.time():
		return result
	lastRefresh = time.time()

	oldUsers = cachedUsers
	cachedUsers = []
	for idx, user in enumerate(oldUsers):
		if user['id'] in cachedForFirstTime: continue
		newCache = getStudData(user, idx)
		cachedUsers.append(newCache)
		if newCache['id'] in requestedIdxs:
			result[requestedIdxs.index(newCache['id'])] = newCache
	print(f'post-cached-{len(cachedUsers)=}')

	return result


def get_first_exam_final_mark(user: dict):
	# Use .get() to provide a default empty list if 'projects_users' key is missing
	exams = [p for p in user.get('projects_users', []) if "exam" in p['project']['slug'].lower() and p['final_mark'] is not None]
	return exams[0]['final_mark'] if exams else None

def sort_by_exam_final_grade_and_login(users: "List[dict]"):
	return sorted(users, key=lambda user: user['average_final_mark'], reverse=True)

def get_average_final_mark(user):
	exams = user.get('currentExams', [])
	total = sum([e['final_mark'] for e in exams if e['final_mark'] is not None or 0])
	if len(exams) == 0:
		return 0
	return total / len(exams)

@app.route("/")
def Homepage():
	students = StudentsAPI()
	if len(students) == 0:
		return render_template("index.html", students=[])

	studentKeys = [str(i).lower() for i in students[0].keys()]
	args = request.args
	filtered = students
	checkForFinalExam = False
	examNameFilter = "exam"
	for arg,val in args.items():
		if arg == "finalcheck":
			checkForFinalExam = True
			continue
		if arg == "exam":
			examNameFilter = val
			continue
		print(f"{arg=}\t{val=}\tpre-{len(filtered)=}")
		filtered = [stud for stud in filtered
			if (val == nested(stud, arg)
					or ((isinstance(nested(stud, arg), list) or isinstance(nested(stud, arg), str)) and conditional(nested(stud, arg), val))
					or (not (isinstance(nested(stud, arg), list) or isinstance(nested(stud, arg), str))  and conditional(nested(stud, arg), val))
					or (isinstance(nested(stud, arg), bool) and val in ["true", "false"] and conditional(nested(stud, arg), "True" if val == "true" else "False"))
			)
		]
	print(f'{len(filtered)=}')
	result = filtered
	if checkForFinalExam:
		result = invalidateCache(filteredList=result)
		print(f'invalidated-{len(result)=}')
	for user in result:
		user['currentExams'] = [e for e in user.get('currentExams', []) if examNameFilter in e['project']['slug'].lower()]
		user['average_final_mark'] = get_average_final_mark(user)
	result = sort_by_exam_final_grade_and_login(result)
	return render_template("index.html", students=result)

#-------------------------------------------------------------------------------

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/static/<file>')
def static_files(file):
    return send_from_directory(os.path.join(app.root_path, 'static'), file)

@app.route("/<page>")
def Other(page):
	return render_template(f"{page}.html")

if __name__ == '__main__':
	app.run(debug=False, host='0.0.0.0', port=SERVER_PORT)