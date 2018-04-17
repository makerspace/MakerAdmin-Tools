#!/usr/bin/python3
import requests
import argparse
import csv
import json
from datatime import datetime, timezone

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
        return requests.post('https://' + self.host + "/" + path, json=payload, headers=headers)

    def put(self, path, payload):
        headers = {"Authorization": "Bearer " + self.key}
        return requests.put('https://' + self.host + "/" + path, json=payload, headers=headers)

print(env["API_BEARER"])
gateway = APIGateway("api.makeradmin.se", env["API_BEARER"])

csvfile = open('startpaket.csv')
open_orders_reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')

col_field_map = {
    "Receiver Name":"name", 
    "Email":"email", 
    "Receiver Phone Number":"phone", 
    "Receiver Address":"address_street", 
    "Receiver Address 2nd Line":"address_extra", 
    "Receiver Zipcode":"address_zipcode", 
    "Receiver City":"address_city", 
    "Receiver Country":"address_country", 
    "Note":"note"
}

open_orders = []
for order in open_orders_reader:
    open_orders.append(order)

order_member_data = {}
for order in open_orders:
    if order["Order Number"] != None and order["Order Number"] != "":
        if "Receiver Name" in order and order["Receiver Name"]:
            order_member_data[order["Order Number"]] = order

possible_new_members = []
for member in open_orders:
    if (member["Order Number"] in order_member_data) and (member["Line Item: Product Title"] == "Startpaket" or member["Line Item: Product Title"] == "Medlemsavgift"):
        print(member["Order Number"])
        member_data = order_member_data[member["Order Number"]]
        new_member = {}
        for col_name, field in col_field_map.items():
            print(field, ": ",member_data[col_name])
            new_member[field] = member_data[col_name]
        if new_member:
            possible_new_members.append(new_member)

possible_new_members.sort(key=lambda member: member["name"].lower())
abort = False
while possible_new_members:
    for idx, member in enumerate(possible_new_members):
        print(idx, ": ", member["name"], " <", member["email"], ">")

    member_input = input("Which member do you want to create? (enter number or 'q' to quit)")
    try:
        if member_input == 'q':
            abort = True
        else:
            number = int(member_input)
            if number < len(possible_new_members):
                new_member_request = possible_new_members[number]
                name_split = new_member_request["name"].split(" ",1)
                new_member_request["firstname"] = name_split[0]
                new_member_request["lastname"] = name_split[1]
                new_member_request["created_at"] = datetime.now(timezone.utc).isoformat()
                new_member_request["updated_at"] = datetime.now(timezone.utc).isoformat()
                print(json.dumps(new_member_request,indent=4));
                confirm_create = input("Do you really wish to create the above member? ('y' to create)")
                if confirm_create and confirm_create[0].lower() == 'y':
                    rpost = gateway.post("membership/member", payload = new_member_request)
                    assert rpost.ok, rpost.text
                    print("Created member ", new_member_request["name"])
                    del possible_new_members[number]
    except ValueError:
        print("Enter a number!")

    if abort:
        break

print("Done")



