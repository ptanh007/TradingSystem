import os

# *****************************
# Environment specific settings
# *****************************

# DO NOT use "DEBUG = True" in production environments
DEBUG = True

# DO NOT use Unsecure Secrets in production environments
# Generate a safe one with:
#     python -c "from __future__ import print_function; import string; import random; print(''.join([random.choice(string.ascii_letters + string.digits + string.punctuation) for x in range(24)]));"
SECRET_KEY = 'MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAI1zSuEJ5OfembK+zIUNQGBd+Z/iEjWwtETTeeBG0VxJXXu+9b9z63XUnsZUfC6kCYbJZZbCZsEUlnGeoHtSI1MCAwEAAQ=='

# SQLAlchemy settings
SQLALCHEMY_DATABASE_URI = 'sqlite:///../userdb.sqlite'
SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids a SQLAlchemy Warning
SESSION_TYPE = 'sqlalchemy'

# Flask-Mail settings
# For smtp.gmail.com to work, you MUST set "Allow less secure apps" to ON in Google Accounts.
# Change it in https://myaccount.google.com/security#connectedapps (near the bottom).
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_SSL = False
MAIL_USE_TLS = True
MAIL_USERNAME = 'developer.qtdata@gmail.com'
MAIL_PASSWORD = 'qtmember@2020'
MAIL_DEFAULT_SENDER = '"QT-TradingSystem" <members.qtdata@gmail.com>'
ADMINS = [
    '"Admin One" <members.qtdata@gmail.com>',
    ]
