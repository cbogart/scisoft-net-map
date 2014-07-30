# How to run tests

Before running tests make sure that you have WebTest library installed:
Execute: `pip install WebTest`. This step is optional, since it should be installed during initial setup.

Before you begin, please make sure you have entered your virtual environment by:
```
$> cd SNM/www
$> . ./env/bin/activate
(env) $>
```

1. Navigate to: `cd SNM/www/SNM-web/`
2. Execute: `python setup.py test -q`:
```
..............
----------------------------------------------------------------------
Ran 14 tests in 0.498s

OK
```


# Coverage

Another way to get more detailed results is:

1. Navigate to: `cd SNM/www/SNM-web/test`
2. Run `./run_test.sh`
3. Navigate to `cd SNM/www/SNM-web/snmweb/test_output` and open `index.html` with any browser
