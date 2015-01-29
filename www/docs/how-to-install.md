
#How to install the web-site for development

Step 0. Clone the repo and navigate to the `SNM/www` folder

Step 1. Install virtenv if needed: `sudo easy_install virtualenv`

Step 2. Create virtual environment in this folder using `virtualenv env` command.
Sample output: 
```
New python executable in /home/nix/env/bin/python
Installing setuptools, pip...done.
```

Step 3. Enter the virtual environment: `source env/bin/activate`. (Use `deactivate` to leave it)
That will result in :
```
$ source env/bin/activate
(env) $
```

Step 4a. `easy_install "pyramid==1.5.1"`

Step 4b. 'pip install numpy'

Step 5. `cd SNM-web`

Step 6. `python setup.py develop`

Leave this instructions and proceed with `how-to-setup-database.md` in order to install mongodb and put sample data in it.
Then get back with Step 7 of current instructions

Step 7. Run web server: `pserve development.ini`

Step 8. To leave virtual env type `deactivate`

# How to start web-server for development

Step 3. Enter virtenv
Step 5. Go to `cd SNM/www/SNM-web`
Step 6. Copy configuration.ini to `production.<platform>.ini` or `development.<platform>.ini` and adjust the settings as needed.   If you
have a Google Analytics key, fill it in.
Step 7. Run serve `pserve configuration.ini`

# P.S.

You can also find it useful `pserve --reload --monitor-restart   development.ini`.
It will automatically reload or restart the serve if code has changed or if server failed.
