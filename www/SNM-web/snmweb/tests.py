import unittest

from pyramid import testing


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_view_home(self):
        from .views import view_home
        request = testing.DummyRequest()
        response = view_home(request)
        self.assertEquals(response["status"], "200 OK")


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        from snmweb import main
        app = main({})
        from webtest import TestApp
        self.testapp = TestApp(app)

    def tearDown(self):
        del self.testapp

    def test_root(self):
        res = self.testapp.get("/", status=200)
        self.assertTrue("<h1>Scientific Network Map</h1>" in res.body)

class ApiFunctionalTests(unittest.TestCase):
    def setUp(self):
        from snmweb import main
        app = main({})
        from webtest import TestApp
        self.testapp = TestApp(app)

    def tearDown(self):
        del self.testapp

    def test_apps(self):
        res = self.testapp.get("/api/apps", status=200)
        import json
        jsonRes = json.loads(res.body)
        print(jsonRes["status"])
        self.assertEqual(jsonRes["status"], "OK1")
