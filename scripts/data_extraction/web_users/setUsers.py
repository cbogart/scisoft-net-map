#!/usr/bin/python
#
# Authors:
#  Chris Bogart, Nikita Chepanov, Biao "Leo" Ma, Svyatoslav "Slava" Kovtunenko
#
from passlib.apps import custom_app_context as pwd_context
from pymongo import Connection

def addUser(db, userid, password):
    c = Connection()
    c[db]["web_users"].save({
	"userid": userid,
	"password": pwd_context.encrypt(password) })

if __name__ == "__main__":
    addUser("snm-web", "guest", "*******")
