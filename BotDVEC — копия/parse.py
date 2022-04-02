import json
import csv
import lxml
import requests
from bs4 import BeautifulSoup

from datetime import datetime, timedelta

import smtplib
import ssl

session = requests.session()


def get_info(req):
    global session

    headers = {
        'User-Agent': 'cron',
        'X-Requested-With': 'XMLHttpRequest'
    }
    r = session.post('https://www.dvec.ru/nerungri/private_clients/pokazaniya/index.php', data=req, headers=headers)
    res = r.content
    soup = BeautifulSoup(res, 'lxml')
    try:
        #     res = json.loads(r.content)
        #
        #     if not res['ok']:
        #         print(res['error'])
        #         return []
        #     else:
        #         res = res['payload']
        #

        res = {
            'ok': True,
            "answ": " ".join(soup.find('table', class_='table-data2').text.split()),
            "step": soup.find(id="step")['value'],
            "sessionkey": soup.find(id="sessionkey")['value'],
            "reading1": soup.find(id="reading1")['value']
        }
    except Exception as ex:
        res = {
            'ok': False,
            "alert": soup.find('div', class_='card').text
        }

    return res


def set_reading(req):
    global session

    headers = {
        'User-Agent': 'cron',
        'X-Requested-With': 'XMLHttpRequest'
    }
    r = session.post('https://www.dvec.ru/nerungri/private_clients/pokazaniya/index.php', data=req, headers=headers)
    res = r.content
    soup = BeautifulSoup(res, 'lxml')
    mpi = soup.find('div', class_='wysiwyg').text
    print(mpi)
    # try:
    #     res = json.loads(r.content)
    #
    #     if not res['ok']:
    #         print(res['error'])
    #         return []
    #     else:
    #         res = res['payload']
    #
    # except Exception as ex:
    #     print("Error parse response depots", ex)
    #     raise Exception

    return mpi


if __name__ == '__main__':
    req = {
        "account": '012044743',
        "meter": '14027470',
        "branch": 'aes',
        "step": '1'
    }
    try:

        titles = get_info(req)
        print(titles)
    except Exception as ex:
        print("Fatal ", ex)
    finally:
        session.close()
