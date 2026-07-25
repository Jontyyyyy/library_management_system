# -----------------------------------------------------------------------
# Configuration for the Library Management System
#
# Locally: just edit the fallback values below (after the "or" on each
#          line) to match your MySQL setup — no environment variables
#          needed.
# Deployed: every value can be overridden with an environment variable
#          of the same name, which is how config.py stays out of your
#          database password when you push this to GitHub.
# -----------------------------------------------------------------------

import os

DB_HOST = os.environ.get("DB_HOST") or "localhost"
DB_PORT = int(os.environ.get("DB_PORT") or 3306)
DB_USER = os.environ.get("DB_USER") or "root"
DB_PASSWORD = os.environ.get("DB_PASSWORD") or "your_mysql_password"
DB_NAME = os.environ.get("DB_NAME") or "library_db"

# Set DB_SSL=true when connecting to a cloud database (e.g. TiDB Cloud)
# that requires TLS. Leave unset/false for a local MySQL install.
DB_SSL = (os.environ.get("DB_SSL") or "false").lower() == "true"

# Used to sign session cookies. Change this to any random string
# before deploying anywhere other than your own machine — see
# DEPLOYMENT.md for a one-line command that generates one.
SECRET_KEY = os.environ.get("SECRET_KEY") or "change-this-to-a-long-random-string"

# Days a book can be borrowed before it's due back
LOAN_PERIOD_DAYS = int(os.environ.get("LOAN_PERIOD_DAYS") or 14)

# Fine charged per day a book is returned late
FINE_PER_DAY = float(os.environ.get("FINE_PER_DAY") or 0.50)
