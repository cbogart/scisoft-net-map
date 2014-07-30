# How to restart production server

1. First ssh to the server, e.g. `ssh your_login@sci-net-map.isri.cmu.edu`
2. Enter super-user mode `su -`
3. Enter wwwuser mode `su - wwwuser`
4. Navigate to `cd /var/www/SNM/www`, where `/var/www/SNM` is git root folder.
5. Get updates: `git pull origin master`
6. Kill `pserve` process, remove `pid` and `log` files in `/var/www` folder.
NB: It's definitely not the most optimal way to do it.
7. Enter virtual env: `cd /var/www` then `. ./environments/env/bin/activate`
8. `cd SNM/www/SNM-web`
9. `pserve production.ini start --daemon --pid-file=/var/www/5000.pid --log-file=/var/www/5000.log --monitor-restart`


NB: Depending on the purpose it could be usefull to run `db_sample.py`script in order to refresh the database.
Be warned, that the script populates the database with sample data wiping out all previous data.

0. Make sure you're in env mode, step 7 above.
1. cd `/var/www/SNM/www/SNM-web/sample_data`
2. Execute `python db_sample.py snm`
where `snm` is the name of production database as in `production.ini` file
```
(env)wwwuser@sci-net-map:/var/www/SNM/www/SNM-web/sample_data$ python db_sample.py snm
Using database: `snm`. You can specidy db with first argument
All data from `snm` will be erased.
Press Enter to continue...

```
