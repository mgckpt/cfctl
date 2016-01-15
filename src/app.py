#!/usr/bin/env python3

from cfctl import *

import cred
a = Account(cred.email, cred.token)

for z in a.list_zones():
    zone = Zone(z, a)
    zone.data = zone.details()
    print(zone.data["name"])
