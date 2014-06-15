
#How to install pyramide

Step 1. Install virtenv if needed: `sudo easy_install virtualenv`

Step 2. Create virtual environment in this folder `virtualenv env` you will see:
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

Step 4. `easy_install "pyramid==1.5.1"`

Step 5. `cd SNM-web`

Step 6. `python setup.py develop`

Step 7. Run web server: `pserve development.ini`

Step 8. To leae virtual env type `deactivate`

# How to start web-server

Step 3. 
Step 5.
Step 7.
