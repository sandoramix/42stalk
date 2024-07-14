import json
import logging
import os
from flask import Flask, render_template, request, send_from_directory

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

@app.route("/")
def Homepage():
	return render_template("index.html")


@app.route("/students")
def StudentsPage():
	students = StudentsAPI()
	if len(students) == 0:
		return render_template("students.html", students=[])

	studentKeys = [str(i).lower() for i in students[0].keys()]
	args = request.args
	filtered = students
	for arg,val in args.items():
		if arg.lower() not in studentKeys:
			continue
		print(f"{arg=}\t{val=}\t{len(filtered)=}")
		filtered = [stud for stud in filtered
	   		if (val == stud[arg]
			or ((isinstance(stud[arg], list) or isinstance(stud[arg], str)) and val in stud[arg]))
		]
	print(f'{len(filtered)=}')
	return render_template("students.html", students=filtered)

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
	app.run(debug=True, host='0.0.0.0', port=SERVER_PORT)