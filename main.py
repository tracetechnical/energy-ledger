#!/usr/bin/env python
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta

ADD_LEDGER_URL = "http://houseura.io.home/api/rest/ledgeradd"

def round_to_nearest_minute(dt):
    seconds = dt.second
    if seconds >= 30:
        dt += timedelta(minutes=1)
    return dt.replace(second=0, microsecond=0)

def add_to_ledger(type, units, rate, cost):
    session = requests.Session()

    retries = Retry(
        connect=5,
        read=5,
        total=5,
        backoff_factor=1,
        raise_on_status=False,
        status_forcelist=[400, 404, 429, 500, 502, 503, 504]
    )
    timestamp = datetime.now().isoformat()
    data = {"timestamp": timestamp, "cost": cost, "type": type, "rate": rate, "units": units}
    session.mount("https://", HTTPAdapter(max_retries=retries))
    stat = 0
    response = {}
    while stat != 200:
        response = session.post(ADD_LEDGER_URL,data)
        stat = response.status_code
    print(response)

def send_get(url):
    session = requests.Session()

    retries = Retry(
        connect=5,
        read=5,
        total=5,
        backoff_factor=1,
        raise_on_status=False,
        status_forcelist=[400, 404, 429, 500, 502, 503, 504]
    )

    session.mount("https://", HTTPAdapter(max_retries=retries))
    stat = 0
    response = {}
    while stat != 200:
        response = session.get(url)
        stat = response.status_code

    return response

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

IMPORT_URL = "http://httpmqttbridge.io.home/electricity/ess/forward"
EXPORT_URL = "http://httpmqttbridge.io.home/electricity/ess/reverse"
RATE_URL = "http://httpmqttbridge.io.home/electricity/rates/current"
importVal = float(send_get(IMPORT_URL).text)
exportVal = float(send_get(EXPORT_URL).text)
print(f"OPEN IMPORT: {importVal}")
print(f"OPEN EXPORT: {exportVal}")
importTotal = 0
exportTotal = 0
importCost = 0
exportCost = 0
while True:
    try:
        nextImportVal = float(send_get(IMPORT_URL).text)
        nextExportVal = float(send_get(EXPORT_URL).text)
        currentRate = float(send_get(RATE_URL).text)
        if round(nextImportVal,1) != round(importVal,1):
            print(f"NEXT IMPORT: {nextImportVal}")
            lastimport = importVal
            currentimport = nextImportVal
            delta = round(currentimport - lastimport,3)
            cost = delta * currentRate
            print(f"IMPORT: {delta} @ {currentRate}p = +£{round(cost/100,4)}")
            add_to_ledger("IMPORT", delta, currentRate, cost/100)
            importCost += cost/100
            importTotal += delta
            print(f"IM:£{round(importCost,2)}")
            importVal = nextImportVal
        if round(nextExportVal,1) != round(exportVal,1):
            print(f"NEXT EXPORT: {nextExportVal}")
            lastexport = exportVal
            currentexport = nextExportVal
            delta = round(currentexport - lastexport,3)
            cost = delta * currentRate
            print(f"EXPORT: {delta} @ {currentRate}p = -£{round(cost/100,4)}")
            add_to_ledger("EXPORT", delta, currentRate, -cost/100)
            exportCost += cost/100
            exportTotal += delta
            print(f"EX:£{round(exportCost,2)}")
            exportVal = nextExportVal
    except:
        print("Ex")