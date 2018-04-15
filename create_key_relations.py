#!/usr/bin/python3
import requests;
import argparse

# Read the .env file
env = {s[0]: (s[1] if len(s) > 1 else "") for s in (s.split("=") for s in open(".env").read().split('\n'))}

class APIGateway:
    def __init__(self, host, key):
        self.host = host
        self.key = key

    def get(self, path, payload=None):
        headers = {"Authorization": "Bearer " + self.key}
        return requests.get('https://' + self.host + "/" + path, params=payload, headers=headers)

    def post(self, path, payload):
        headers = {"Authorization": "Bearer " + self.key}
        print(payload)
        resp = requests.post('https://' + self.host + "/" + path, json=payload, headers=headers)
        print(resp)
        return resp

    def put(self, path, payload):
        headers = {"Authorization": "Bearer " + self.key}
        return requests.put('https://' + self.host + "/" + path, json=payload, headers=headers)


gateway = APIGateway("api.makeradmin.se", env["API_BEARER"])

page = 22
abort = False
while True:
    r = gateway.get("keys?sort_order=asc&sort_by=key_id&page=" + str(page))
    assert r.ok, r.text
    
    key_resp = r.json()
    keys = key_resp["data"]
    pages = key_resp["last_page"]
    print("Page "+str(page)+" contains "+str(len(keys))+" keys") 
    for key in keys:
        member_resp_json = gateway.get('membership/member?member_number={0}'.format(key["title"]))
        assert member_resp_json.ok
        member_data_arr = member_resp_json.json()["data"]
        assert len(member_data_arr) == 1
        member_data = member_data_arr[0]
        member_name = member_data["firstname"] + " " + member_data["lastname"]

        relations_resp_json = gateway.get('relations?param=/keys/{0}&matchUrl=/membership/member/(.*)'.format(key["key_id"]))
        assert relations_resp_json.ok
        relations_resp = relations_resp_json.json()
        relations_data_arr = relations_resp["data"]
        assert len(relations_data_arr) <= 1
        member_matches = "NO RELATION"
        if len(relations_data_arr) == 1:
            relations_match_str = relations_data_arr[0]["matches"][1]
            member_matches = "assigned" if relations_match_str == member_data["member_id"] else "MISSMATCH"
        else:
            rpost = gateway.post("relation", payload = {
                "url1": "/membership/member/{0}".format(member_data["member_id"]),
                "url2": "/keys/{0}".format(key["key_id"]),
            })
            assert rpost.ok
            print(rpost)
        
        print("\t"+key["key_id"] + " " + member_matches + ", " + key["title"] + ": " + member_name)
    page += 1;
    if page > pages or abort:
        break

print("Done")

