from mock import patch
import unittest
from pyramid import testing
import mongoengine
from db_objects import *


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings={"db_name": "snm-test"})

    def tearDown(self):
        testing.tearDown()

    def test_view_home(self):
        from .views import view_home
        request = testing.DummyRequest()
        response = view_home(request)
        self.assertEquals(response["status1"], "200 OK")


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        from snmweb import main
        settings = {"db_name": "snm-test"}
        app = main({}, **settings)
        from webtest import TestApp
        self.testapp = TestApp(app)
        self.config = testing.setUp()

    def tearDown(self):
        del self.testapp

    def test_root(self):
        res = self.testapp.get("/", status=200)
        self.assertTrue("Scientific Network Map" in res.body)

    @patch.object(mongoengine.queryset.QuerySet, "first")
    def test_get_app(self, mock_first):
        mock_first.return_value = Application(title="Euler", description="a", image="a", version=1.0)

        res = self.testapp.get("/application/Euler", status=200)

        self.assertTrue("Euler" in res.body)

    @patch.object(mongoengine.queryset.QuerySet, "first")
    def test_app_usage(self, mock_first):
        mock_first.return_value = Application(title="Euler", description="a", image="a", version=1.0)

        res = self.testapp.get("/application/Euler/usage",
                               status=200)

        self.assertTrue("<svg>" in res.body)
        self.assertTrue("Euler" in res.body)

    def test_compare(self):
        res = self.testapp.get("/compare",  status=200)
        self.assertTrue("Compare" in res.body)

    def test_overview(self):
        res = self.testapp.get("/overview",  status=200)
        self.assertTrue("<h1>" in res.body)

    def test_about(self):
        res = self.testapp.get("/data-sources",  status=200)
        self.assertTrue("source" in res.body)

    def test_browse(self):
        res = self.testapp.get("/browse",  status=200)
        self.assertTrue("<h1>" in res.body)


class ApiFunctionalTests(unittest.TestCase):
    def setUp(self):
        from snmweb import main
        settings = {"db_name": "snm-test"}
        app = main({}, **settings)
        from webtest import TestApp
        self.testapp = TestApp(app)
        from json import loads
        self.parse = loads
        self.config = testing.setUp(settings={"db_name": "snm-test"})

    def tearDown(self):
        del self.testapp

    def test_api_root(self):
        res = self.testapp.get("/api", status=200).body
        res = self.parse(res)
        self.assertEqual(res["status"], "OK")

    def test_api_unknown_category(self):
        res = self.testapp.get("/api/SOME_UNKNOWN_STUFF", status=200).body
        res = self.parse(res)
        self.assertEqual(res["status"], "ERROR")

    def test_api_apps(self):
        res = self.testapp.get("/api/apps", status=200).body
        res = self.parse(res)
        self.assertEqual(res["status"], "OK")
        self.assertTrue(isinstance(res["data"], list))

    def test_api_get_app(self):
        res = self.testapp.get("/api/apps/SOME_UNKNOWN_ID", status=200).body
        res = self.parse(res)
        self.assertEqual(res["status"], "OK")
        #TODO: check for unknown id later

    def test_api_stat(self):
        res = self.testapp.get("/api/stat", status=200).body
        res = self.parse(res)
        self.assertEqual(res["status"], "OK")
        self.assertTrue(isinstance(res["data"], list))

    def test_api_stat_unknown(self):
        res = self.testapp.get("/api/stat/SOME_UNKNOWN_STUFF", status=200).body
        res = self.parse(res)
        self.assertEqual(res["status"], "ERROR")

#TODO: Commented out due to hardcoded constants that cannot be tested at this
#  time. Should be fixed once we have real data
"""
    def test_api_stat_usage(self):
        res = self.testapp.get(
            "/api/stat/usage_over_time",
            status=200,
            params={"id": "5b0209c8d3"}).body
        print res

        res = self.parse(res)
        self.assertEqual(res["status"], "OK")

        res = self.testapp.get(
            "/api/stat/usage_over_time",
            status=200,
            params={"id": "UNKNOWN_APP_ID"}).body

        res = self.parse(res)
        self.assertEqual(res["status"], "ERROR")


        for arg in ["day", "week", "month"]:
            res = self.testapp.get(
                "/api/stat/usage_over_time",
                status=200,
                params={"group_by":arg}).body
            res = self.parse(res)
            self.assertEqual(res["status"], "OK")
            self.assertTrue(isinstance(res["data"], list))
"""
