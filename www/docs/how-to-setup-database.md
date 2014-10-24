
#How to setup database

Before you begin, please make sure you have entered your virtual environment by:
```
$> cd SNM/www
$> . ./env/bin/activate
(env) $>
```

1. Install mongo: `sudo apt-get install mongodb` if on Ubuntu. Otherwise use [the link](http://docs.mongodb.org/manual/installation/)

#To import data from another valid copy of the database

1. On the machine with the valid database:
  - `mongodump --db <dbname> --collection scimapInfo --out dump123`
2. Copy `dump123` to the new machine
3. `mongo <dbname> --eval "db.dropDatabase()"`
4. `mongorestore dump123`
