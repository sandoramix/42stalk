from API42 import Api42
from dotenv import load_dotenv, find_dotenv
import os
import logging



load_dotenv(".env")

LOG = logging.getLogger()

ENV = {
	"CLIENT_ID": os.environ['CLIENT_ID'],
	"CLIENT_SECRET": os.environ['CLIENT_SECRET'],
	"SCOPE": os.environ['SCOPE'],
}

_valid_env = True

for key,val in ENV.items():
	if (len(val.strip()) == 0):
		LOG.error(f'ENV VARIABLE [{str(key).upper()}] is not valid')
		_valid_env = False

if not _valid_env:
	LOG.error("INVALID ENVIRONMENT VARIABLES")
	exit(1)

API = Api42(client_id=ENV['CLIENT_ID'], client_secret=ENV['CLIENT_SECRET'], scope=ENV['SCOPE'])
