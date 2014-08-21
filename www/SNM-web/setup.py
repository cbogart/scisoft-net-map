import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.txt")) as f:
    README = f.read()
with open(os.path.join(here, "CHANGES.txt")) as f:
    CHANGES = f.read()

requires = [
    "pyramid",
    "pyramid_jinja2",
    "pyramid_debugtoolbar",
    "passlib",
    "waitress",
    "nose",
    "WebTest",
    "mongoengine",
    "pymongo",
    "mock",
    "coverage"
    ]

setup(name="SNM-web",
      version="0.0",
      description="SNM-web",
      long_description=README + "\n\n" + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author="",
      author_email="",
      url="",
      keywords="web pyramid pylons",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="snmweb",
      entry_points="""\
      [paste.app_factory]
      main = snmweb:main
      """,
      )
