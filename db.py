#SQLite helpers: init, queries, tokens

import sqlite3
import os
from datetime import datetime, timedelta

#sqlite3 is the python inbuilt module that lets you communicate with SQLite engine
#os build the path to app.db reliably regardless of where you run the script
#datetime, timedelta compute token expiry (now + 30 days) and write timestamps 