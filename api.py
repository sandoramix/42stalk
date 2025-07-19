from API42 import Api42
from dotenv import load_dotenv, find_dotenv
import os
import logging



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

API = Api42(client_id=ENV['CLIENT_ID'], client_secret=ENV['CLIENT_SECRET'], scope=ENV['SCOPE'])
