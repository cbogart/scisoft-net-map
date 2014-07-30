from mock import patch
import unittest
from pyramid import testing
import mongoengine

from db_objects import *
from mongoengine import *


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings={"db_name": "snm-test"})

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
        res = self.testapp.get("/about",  status=200)
        self.assertTrue("About" in res.body)

    def test_browse(self):
        res = self.testapp.get("/browse?order=title",  status=200)
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

    def test_api_apps_query(self):
        res = self.testapp.get("/api/apps?query=euler", status=200).body
        res = self.parse(res)
        self.assertEqual(res["status"], "OK")
        self.assertTrue(isinstance(res["data"], list))

    def test_api_apps_ids(self):
        res = self.testapp.get("/api/apps?ids=53cd803a83297424dfe37699", status=200).body
        res = self.parse(res)
        self.assertEqual(res["status"], "OK")
        self.assertTrue(isinstance(res["data"], list))

    def test_api_apps_query_and_ids(self):
        res = self.testapp.get("/api/apps?ids=53cd803a83297424dfe37699&query=euler", status=200).body
        res = self.parse(res)
        self.assertEqual(res["status"], "OK")
        self.assertTrue(isinstance(res["data"], list))

    @patch.object(mongoengine.queryset.QuerySet, "all")
    def test_api_get_app(self, mock_all):
        mock_all.return_value = [Application(id="53cd803a83297424dfe37699", title="Test", description="a", image="a", version=1.0)]

        res = self.testapp.get("/api/apps/Test", status=200).body
        res = self.parse(res)
        self.assertEqual(res["status"], "OK")

    def test_api_stat(self):
        res = self.testapp.get("/api/stat", status=200).body
        res = self.parse(res)
        self.assertEqual(res["status"], "OK")
        self.assertTrue(isinstance(res["data"], list))

    def test_api_stat_data_over_time_no_group_and_id(self):
        res = self.testapp.get("/api/stat/data_over_time").body
        res = self.parse(res)
        self.assertRaises(Exception)

    def test_api_stat_data_over_time_no_id(self):
        res = self.testapp.get("/api/stat/data_over_time?group_by=daily").body
        res = self.parse(res)
        self.assertRaises(Exception)

    def test_api_stat_data_over_time_no_group(self):
        res = self.testapp.get("/api/stat/data_over_time?id=53cd803a83297424dfe37699").body
        res = self.parse(res)
        self.assertRaises(Exception)

#    @patch.object(mongoengine.queryset.QuerySet, "all")
#    @patch.object(Application, "title")
#    @patch.object(Usage, "to_mongo")
#    def test_api_stat_usage_over_time(self, mock_all, mock_titile, mock_to_mongo):
#        mock_all.return_value = [Usage("53d865d18329745cf0ad87d1", application = "53d865d08329745cf0ad87b3", daily = [{ "y" : 0, "x" : "2012-10-31" }])]
#        mock_title.return_value = "App"
#        mock_to_mongo.return_value = {"daily" : [{ "y" : 0, "x" : "2012-10-31"}]}
#
#        res = self.testapp.get("/api/stat/usage_over_time?id=53d865d08329745cf0ad87b3&group_by=day").body
#        res = self.parse(res)
#        self.assertEqual(res["status"], "OK")
#        self.assertTrue(isinstance(res["data"], list))

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
