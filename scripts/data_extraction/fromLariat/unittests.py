import json
import pdb
from UsageCache import UsageCache, freshDb

from pymongo import MongoClient, Connection

c = Connection()
dest = freshDb(c, "snm-cooked-test")

with open("testdata.json") as f:
    testdata = json.load(f)


cache = UsageCache(dest, True)
assert len(cache.apps) == 0, "Empty cache has apps"
assert cache.max_co_uses["static"] == 0, "Empty cache has static use count"
assert cache.max_co_uses["logical"] == 0, "Empty cache has logical use count"


def right_after_first(cache):
    assert len(cache.apps) == 11, "Did not add first app"
    assert cache.apps["datasets"]["usage"]["2014-10-14"] == 1
    assert len(cache.apps["datasets"]["user_list"]["2014-10-14"]) == 1
    assert cache.max_co_uses["static"] == 1
    assert cache.max_co_uses["logical"] == 1
    assert cache.apps["graphics"]["co_occurence"]["grDevices"]["static"] == 1
    assert cache.apps["graphics"]["co_occurence"]["grDevices"]["logical"] == 1

def right_after_second(cache):
    assert len(cache.apps) == 11, "Did not add second app"
    assert cache.max_co_uses["static"] == 2
    assert cache.max_co_uses["logical"] == 2

def right_after_tenth(cache):
    assert len(cache.apps) == 11, "Did not add tenth app"
    assert cache.max_co_uses["static"] == 10
    assert cache.max_co_uses["logical"] == 10

def fully_equal(cache1, cache2):
    assert len(cache1.apps) == len(cache2.apps), "Same number of apps at least!"


cache.registerPacket(testdata.pop())
assert cache.dirty, "Should be dirty1"
right_after_first(cache)
assert cache.dirty, "Should be dirty2"
cache.saveToMongo()
assert not(cache.dirty )
cache2 = UsageCache(dest, True)
assert not(cache2.dirty )
right_after_first(cache2)


cache.registerPacket(testdata.pop())
right_after_second(cache)
assert cache.dirty 
cache.saveToMongo()
assert not(cache.dirty )
cache2 = UsageCache(dest, True)
right_after_second(cache2)

cache.registerPacket(testdata.pop())
assert cache.dirty 
cache.registerPacket(testdata.pop())
cache.registerPacket(testdata.pop())
cache.registerPacket(testdata.pop())
cache.registerPacket(testdata.pop())
cache.registerPacket(testdata.pop())
cache.registerPacket(testdata.pop())
cache.registerPacket(testdata.pop())
right_after_tenth(cache)
cache.saveToMongo()
cache2 = UsageCache(dest, True)
right_after_tenth(cache2)

fully_equal(cache, cache2)

for p in testdata:
    cache.registerPacket(p)
cache.saveToMongo()
