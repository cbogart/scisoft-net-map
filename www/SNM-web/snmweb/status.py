import os

#
#  Very specific check for status of website, that's
#  dependent on exact filenames of registration and
#  server INI files, etc.
#
#  This is to monitor the uptime of the site remotely.
#
def check_site_status(sci_platform):
    ps = os.popen("ps -Af")
    pslines = ps.read()
    servername = "pserve production." + sci_platform + ".ini"
    servers = servername in pslines
    registries = "python listenForRPackets.py" in pslines
    if (sci_platform == "R"):
        if (servers and registries):
            return "UP"
        elif (not registries):
            return "REGISTRY DOWN"
        else:
            return "SERVERS DOWN"   # Won't happen if this func is called by server
    else:
        if (servers):
            return "UP"
        else:
            return "SERVERS DOWN"

if __name__ == "__main__":
    import sys
    sci_platform = "R" if len(sys.argv) == 1 else sys.argv[1]
    print sci_platform + ": " + check_site_status(sci_platform)
