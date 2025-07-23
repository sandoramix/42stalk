# 42 Stalk

This is a simple Flask app that fetches students from the 42 API and displays them in a web interface.
The good part is that there is a filtering system that allows you to filter by exams, projects, by average final mark, and every other field that is available in the student's JSON object.

## Installation

1. Install Python 3.10 or newer
2. Run `init.sh` to create a virtual environment and install dependencies
3. Setup your .env with the 42 API credentials
4. Fetch the students data by running `./fetch-students.sh` or `./fetch-students.sh <CAMPUS_ID>`
5. Run the app by running `./run-server.sh`
6. Enjoy the stalk!
