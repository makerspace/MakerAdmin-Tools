#!/usr/bin/python3
import requests;
import argparse
import csv

# Read the .env file
env = {s[0]: (s[1] if len(s) > 1 else "") for s in (s.split("=") for s in open(".env").read().split('\n'))}

class APIGateway:
    def __init__(self, host, key):
        self.host = APIGateway._ensure_protocol(host)
        self.key = key
        print(self.host)

    def get(self, path, payload=None):
        headers = {"Authorization": "Bearer " + self.key}
        return requests.get(self.host + "/" + path, params=payload, headers=headers)

    def _ensure_protocol(host):
        if not host.startswith("http://") and not host.startswith("https://"):
            host = "https://" +  host
        return host


gateway = APIGateway(env["API_HOST"], env["API_BEARER"])

page = 1
abort = False

member_data_fields = ['member_number', 'firstname', 'lastname']
all_members = {}
while True:
    r = gateway.get("membership/member?sort_order=asc&sort_by=member_id&per_page=1000&page=" + str(page))
    assert r.ok, r.text

    members_resp = r.json()
    members = members_resp["data"]
    page_count = members_resp["last_page"]
    print("Page "+str(page)+" contains "+str(len(members))+" members")
    for member in members:
        current_member = {field: member[field] for field in member_data_fields}
        all_members[str(member['member_number'])] = current_member
    page += 1;
    if page > page_count or abort:
        break

page = 1
active_member_data = [];

while True:
    r = gateway.get("keys?sort_order=asc&sort_by=key_id&per_page=1000&page=" + str(page))
    assert r.ok, r.text

    key_resp = r.json()
    keys = key_resp["data"]
    page_count = key_resp["last_page"]
    print("Page "+str(page)+" contains "+str(len(keys))+" keys")
    for key in keys:
        member_data = all_members[key["title"]]
        active_member = {field: member_data[field] for field in member_data_fields}
        active_member['enddate'] = key['enddate']

        active_member_data.append(active_member)
    page += 1;
    if page > page_count or abort:
        break

if not abort:
    export_data_fields = ['member_number', 'firstname', 'lastname', 'enddate']
    with open('member_lab_enddate.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=export_data_fields)
        writer.writeheader()
        for member in active_member_data:
            writer.writerow({field: member[field] for field in export_data_fields})

print("Done")

