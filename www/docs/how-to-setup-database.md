
#How to setup database

Before you begin, please make sure you have entered your virtual environment by:
```
$> cd SNM/www
$> . ./env/bin/activate
(env) $>
```

1. Install mongo: `sudo apt-get install mongodb` if on Ubuntu. Otherwise use [the link](http://docs.mongodb.org/manual/installation/)
2. Navigate to `SNM/www/SNM-web/sample_data` 
3. Execute: `python db_sample.py`. This will populate the database with sample data from `db_sample.json` and `sample_usage` / `sample_usage_users` folders.

```
(env)$> python db_sample.py
Using database: `snm-test`. You can specidy db with first argument
All data from `snm-test` will be erased.
Press Enter to continue...
...
```
