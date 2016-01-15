#! env python3

from datetime import time, timedelta, datetime
from time import sleep

import requests, json

useragent = "OnlyFoolAndHorses"
version = "dev"

class Account(object):
    def __init__(self, email, key, count=True, store=False, nb_wkr=1):
        '''
        Account is the class with all the method that apply to an account.
        "email" and "key" are the credentials required to use the API. If
        "count" is True (recommended), a counter will be created to monitor
        the rate of API calls and slow it cap it to the maximum. If "store"
        is true, a list of zones will be populated automatically (will slow 
        down execution if there is many zones in the account).
        '''
        self.headers = { 'X-Auth-Email': email, 'X-Auth-Key': key,
                            'Content-Type': 'application/json',
                            'User-Agent': useragent + "-" + version }
        
        self.endpoint = "https://api.cloudflare.com/client/v4"

        # Default values for request rate
        self.maxhits = int(1200.0/nb_wkr)
        self.period = 300

        if count:
            self.counter = Counter(self)

        if store:
            self.zones = []
            for i in self.list_zones():
                z = Zone({"id": i["id"], "name": i["name"]}, self)
                self.zones.append(z)
        
    def get(self, suffix, p={}):
        '''
        Send a GET request with the "suffix" following the API endpoint and
        the query strings present in "p"
        '''
        if self.counter:
            self.counter.inc()

        ans = requests.get(self.endpoint+suffix, params=p,
            headers=self.headers)

        #TODO: make the following a debug output
        #print(ans.url)
        #print(ans.text)

        res = self.ans_check(ans)
        content = res["content"]

        if "info" in res.keys():
            info = res["info"]

            if info["page"] < info["total_pages"]:
                if "page" in p.keys():
                    p["page"] += 1
                else:
                    p["page"] = 2
                content += self.get(suffix, p)

        return content

    def post(self, suffix, d, p={}):
        '''
        Send a POST request with the "suffix" following the API endpoint, the
        query strings present in "p", and the data in "d".
        '''
        if self.counter:
            self.counter.inc()

        ans = requests.post(self.endpoint+suffix, params=p,
            headers=self.headers, data=json.dumps(d))

        res, info = self.ans_check(ans)

        return res

    def put(self, suffix, d, p={}):
        '''
        Send a PUT request with the "suffix" following the API endpoint, the
        query strings present in "p", and the data in "d".
        '''
        if self.counter:
            self.counter.inc()

        ans = requests.put(self.endpoint+suffix, params=p,
            headers=self.headers, data=json.dumps(d))

        res, info = self.ans_check(ans)

        return res

    def patch(self):
        print("Not implemented yet")

    def delete(self):
        print("Not implemented yet")

    def list_zones(self, p={}):
        '''
        https://api.cloudflare.com/#zone-list-zones
        '''
        j = self.get("/zones", p)
        return j

    def create_zone(self, name):
        '''
        https://api.cloudflare.com/#zone-create-a-zone
        '''
        print("Not yet implemented")
        
    def search_zone(self, s):
        p = { "name": str(s) }
        return self.list_zones(p)

    def ans_check(self, ans):
        try:
            r = ans.json()
            if not r["success"]:
                c = r["errors"][0]["code"]
                m = r["errors"][0]["message"]
                raise APIError(c, m)

            res = { "content": r["result"] }

            if "result_info" in r.keys():
                res["info"] = r["result_info"]

            return res

        except APIError as err:
            print(err)

class APIError(Exception):
    def __init__(self, code, mesg):
        self.code = code
        self.mesg = mesg

    def __str__(self):
        c = int(self.code)
        m = str(self.mesg)
        return repr("The API endpoint returned: %d, %s" % (c, m))

class Counter(object):
    def __init__(self, account):
        '''
        Counter is a class to prevent overshooting the API call limit.
        '''
        self.period = account.period
        self.maxhits = account.maxhits
        self.hist = []

    def inc(self):
        '''
        Checks if the number of requests sent over the last <period> is
        below the maximum rate, calculates and waits for the appropriate
        delay if not. Meant to be only used by the Account methods get,
        post, patch, delete.
        '''
        d = timedelta(seconds = self.period)
        self.hist.append(datetime.now())
        
        while self.hist[-1] - self.hist[0] > d:
            self.hist.remove(self.hist[0])
    
        if len(self.hist) >= self.maxhits:
            delay = d - (self.hist[-1] - self.hist[0])
            sleep(delay.total_seconds())

class Zone(object):
    def __init__(self, z, ac, store=False):
        '''
        Zone is the class with all the method that apply to a zone/domain.
        "z" can be any dic that has at least the zone id stored in z["id"].
        "ac" is the Account object the zone belongs to. If "store" is true,
        a list of records will be populated automatically (will slow down
        execution if there is many records in the zone).
        '''
        assert type(ac) is Account
        self.account = ac
        self.data = z
        self.prefix = "/zones/" + self.data["id"]

        if store:
            self.records = []
            for j in self.list_records():
                r = Record({"id": j["id"], "name": j["name"]}, self)
                self.records.append(r)
        
    def activation_check(self):
        '''
        https://api.cloudflare.com/#zone-initiate-another-zone-activation-check
        '''
        print("Not yet implemented")

    def details(self):
        '''
        https://api.cloudflare.com/#zone-zone-details
        '''
        return self.account.get(self.prefix)

    def edit(self):
        '''
        https://api.cloudflare.com/#zone-edit-zone-properties
        '''
        print("Not yet implemented")

    def purge_url(self):
        '''
        https://api.cloudflare.com/#zone-purge-individual-files-by-url-and-cache-tags
        '''
        print("Not yet implemented")

    def purge_tags(self):
        '''
        https://api.cloudflare.com/#zone-purge-individual-files-by-url-and-cache-tags
        '''
        print("Not yet implemented")

    def purge_all(self):
        '''
        https://api.cloudflare.com/#zone-delete-a-zone
        '''
        print("Not yet implemented")

    def delete(self):
        '''
        https://api.cloudflare.com/#zone-delete-a-zone
        '''
        print("Not yet implemented")

    def list_records(self):
        url = self.prefix + "/dns_records"
        return self.account.get(url)

    def create_record(self, t, n, c, ttl=1, proxied=False): 
        # TODO: sanitise!
        url = self.prefix + "/dns_records"
        d = { "type": t, "name": n, "content": c, "ttl": ttl }
        res = self.account.post(url, d)
	# TODO: add object Record
        # if proxied=True, Record.orange()

class Record(object):
    def __init__(self, r, zo):
        '''
        Record is the class with all the method that apply to a DNS record.
        "r" can be any dictionary that has at least the record id stored in
        r["id"]. "zo" is the Zone object the record belongs to.
        '''
        assert type(zo) is Zone
        self.zone = zo
        self.data = r
        self.prefix = self.zone.prefix + "/dns_records/" + self.data["id"]

    def details(self):
        self.data = self.zone.account.get(self.prefix)
        return self.data
        
    def orange(self):
        if self.data["proxiable"] and not self.data["proxied"]:
            self.zone.account.put(self.prefix, {"proxied": True})

    def grey(self):
        if self.data["proxiable"] and self.data["proxied"]:
            self.zone.account.put(self.prefix, {"proxied": False})
