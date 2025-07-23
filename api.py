from API42 import Api42
from dotenv import load_dotenv, find_dotenv
import os
import logging
from os import path
from constants import JSON_CONFIG, JSON_CAMPUSES
import json
import time
import datetime

logging.basicConfig(level=logging.DEBUG)

CONSTANTS = {
	"LAST_FETCH": "lastFetch",
	"DATA": "data",
	"DEFAULT_CAMPUS": "defaultCampus",
	"CAMPUS_EXPIRE_DAYS": "campusDataExpireDays"
}

CONFIG = {
	CONSTANTS['CAMPUS_EXPIRE_DAYS']: 7
}

ALL_CAMPUSES = []
SELECTED_CAMPUS: "dict|None" = None

load_dotenv(".env")

LOG = logging.getLogger()

ENV = {
	"CLIENT_ID": os.environ['CLIENT_ID'] if 'CLIENT_ID' in os.environ else '',
	"CLIENT_SECRET": os.environ['CLIENT_SECRET'] if 'CLIENT_SECRET' in os.environ else '',
	"SCOPE": os.environ['SCOPE'] if 'SCOPE' in os.environ else ''
}

_valid_env = True

for key,val in ENV.items():
	if (len(val.strip()) == 0):
		LOG.error(f'\033[31mERROR: ENV VARIABLE {key} IS NOT SET\033[0m')
		_valid_env = False

if not _valid_env:
	LOG.error("\033[31mERROR: ENV VARIABLES ARE NOT SET CORRECTLY\033[0m")
	exit(1)


def saveConfig():
	try:
		with open(JSON_CONFIG, "w+") as file:
			json.dump(CONFIG, file, indent=2)
			LOG.info(f"Saved config to {JSON_CONFIG}")
	except Exception as e:
		LOG.error(f"Error saving config to {JSON_CONFIG}: {e}")

def loadConfig():
	global CONFIG
	loadedConfig = None
	try:
		changed = False
		if not path.exists(JSON_CONFIG):
			saveConfig()
		with open(JSON_CONFIG, "r+") as file:
			loadedConfig = json.load(file)
			for key, val in CONFIG.items():
				if key not in loadedConfig:
					loadedConfig[key] = val
					LOG.info(f"Fallback to default value for {key} with value {val}")
					changed = True
			CONFIG = loadedConfig
			LOG.info(f"Loaded config from {JSON_CONFIG} !")
			if changed:
				saveConfig()
	except Exception as e:
		LOG.error(f"Error loading config from {JSON_CONFIG}: {e}")


def invalidateCampusCache():
	global CONFIG
	global ALL_CAMPUSES

	def isCampusCacheExpired(lastFetchTimestamp):
		now = datetime.datetime.now()
		delta = now - datetime.datetime.fromtimestamp(lastFetchTimestamp)
		LOG.debug(f"Campus cache is {delta.days} days old")
		return delta.days >= CONFIG[CONSTANTS['CAMPUS_EXPIRE_DAYS']]

	try:
		shouldFetch = False
		try:
			if (path.exists(JSON_CAMPUSES)):
				with open(JSON_CAMPUSES, "r") as file:
					DATA = json.load(file)
					if CONSTANTS['LAST_FETCH'] not in DATA or isCampusCacheExpired(DATA[CONSTANTS['LAST_FETCH']]):
						shouldFetch = True
					else:
						ALL_CAMPUSES = DATA[CONSTANTS["DATA"]]
						LOG.info(f"Loaded campuses from {JSON_CAMPUSES}")
			else:
				LOG.info(f"Campuses cache file {JSON_CAMPUSES} does not exist")
				shouldFetch = True
		except Exception as e:
			LOG.error(f"Error loading campuses from {JSON_CAMPUSES}: {e}")
			shouldFetch = True
		if shouldFetch:
			LOG.info(f"Fetching campuses from API")
			result = API.getAllCampuses()
			with open(JSON_CAMPUSES, "w+") as file:
				final_json = {
					CONSTANTS["LAST_FETCH"]: datetime.datetime.now().timestamp(),
					CONSTANTS["DATA"]: result
				}
				json.dump(final_json, file, indent=2)
				LOG.info(f"Saved campuses to {JSON_CAMPUSES}")
				ALL_CAMPUSES = result
		return True
	except Exception as e:
		LOG.error(f"Error loading campuses from {JSON_CAMPUSES}: {e}")
		return False


def printCampuses():
	global ALL_CAMPUSES
	LOG.info("List of campuses:")
	for campus in sorted(ALL_CAMPUSES, key=lambda k: k['id']):
		id = campus['id']
		name = campus['name']
		LOG.info(f"\t{id=}:\t{name=}")

def selectCampus(id = None):
	global ALL_CAMPUSES
	global SELECTED_CAMPUS
	global CONFIG

	found = False
	if id is not None:
		for campus in ALL_CAMPUSES:
			if campus['id'] == id:
				SELECTED_CAMPUS = campus
				found = True
				break
		if not found:
			LOG.error(f"Selected campus {id=} is not in the list of campuses")
	if not found:
		LOG.info(f"Select a default campus from the list of campuses")
		printCampuses()

		campusesMap = { campus['id']: campus for campus in ALL_CAMPUSES }
		while True:
			try:
				id = int(input("Select a campus ID (write 0 to get a list of campuses): "))
				if id == 0:
					printCampuses()
					continue
				if id in campusesMap:
					SELECTED_CAMPUS = campusesMap[id]
					break
				else:
					LOG.error(f"Invalid campus {SELECTED_CAMPUS}")
			except Exception as e:
				LOG.error(f"Invalid input provided. Try again.")
	if SELECTED_CAMPUS is not None:
		CONFIG[CONSTANTS['DEFAULT_CAMPUS']] = SELECTED_CAMPUS['id']
		LOG.info(f"Selected campus {SELECTED_CAMPUS['id']}: {SELECTED_CAMPUS['name']}")
	saveConfig()

def loadCampuses():
	global ALL_CAMPUSES
	global SELECTED_CAMPUS
	global CONFIG
	if not invalidateCampusCache():
		return False
	if (CONSTANTS['DEFAULT_CAMPUS'] in CONFIG and CONFIG[CONSTANTS['DEFAULT_CAMPUS']] is not None):
		selectCampus(CONFIG[CONSTANTS['DEFAULT_CAMPUS']])
	else:
		selectCampus()

API = Api42(client_id=ENV['CLIENT_ID'], client_secret=ENV['CLIENT_SECRET'], scope=ENV['SCOPE'])

loadConfig()
loadCampuses()
