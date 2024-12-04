import time
from comm import read_plc
import requests
from config import machine_info
from logger import log
import json
from database import CL_DBHelper
from datetime import datetime
import schedule
from models import read_all_models

SEND_DATA = True
HOST_TELE = machine_info['host_tele']
HOST_API = machine_info['host_api']
ACCESS_TOKEN = machine_info['access_token']
URL_TELE = f'http://{HOST_TELE}/api/v1/{ACCESS_TOKEN}/telemetry'
URL_API = f'http://{HOST_API}/create_update_recipe_data'
HEADERS = {"Content-Type": "application/json"}

# variable to hold data globally
GL_DATA = []
GL_PHASE_DATA = {}

# variable for whenever cycle starts or stops
GL_PREV_STATUS = 0
GL_FIRST_TIME = True
db = CL_DBHelper()
GL_RECIPE_ID = 0


# from logger import log

def post_api_data(date_):
    global GL_RECIPE_ID
    payload = db.get_cycle_data()
    # GL_RECIPE_ID = payload[0]
    if payload:
        payload_api = {
            "rd_id": payload[0],
            "date_": payload[1],
            "start_time": payload[2],
            "stop_time": payload[3],
            "machine": payload[4],
            "line": payload[5],
            "recipe_name": payload[6],
            "operator": payload[7]
        }
        log.info(f"Api payload : {payload_api}")
        try:
            response = requests.post(URL_API, json=[payload_api], timeout=2)
            response.raise_for_status()
            log.info(f"Api data sent: {response.status_code}")
            data = db.get_sync_data()
            if data:
                try:
                    for value in data:
                        payload = json.loads(value[0])
                        # payload = ast.literal_eval(value[0])
                        # sending payload in list because it is required in api
                        actual_payload = [payload]
                        log.info(f"Payload to send sync {actual_payload}")
                        sync_req = requests.post(URL_API, json=actual_payload, timeout=2)
                        sync_req.raise_for_status()
                        log.info(f"payload send from sync data : {sync_req.status_code}")
                except Exception as e:
                    log.error(f"[-] Error in sending SYNC Cycle time data {e}")
                else:
                    db.delete_sync_data()
            else:
                log.info(f"Synced data is empty")
        except Exception as e:
            log.error(f"Error: {e}")
            db.add_sync_data(payload_api)
    else:
        log.info(f"Payload is None")


def post_data():
    global GL_DATA, GL_RECIPE_ID
    # date_ = datetime.today().strftime("%F")
    payload = db.get_cycle_data()
    GL_RECIPE_ID = payload[0]
    if GL_DATA:
        payload = {
            "air_flow_status": GL_DATA[0],
            "door_status": GL_DATA[1],
            "temp_high_limit": GL_DATA[2],
            "temp_low_limit": GL_DATA[3],
            "temp_value": GL_DATA[5],
            "recipe_name": GL_DATA[6],
            "target_temp": GL_DATA[7],
            "recipe_id": GL_RECIPE_ID
        }
        if SEND_DATA:
            try:
                log.info(f"Payload : {payload}")
                send_req = requests.post(URL_TELE, json=payload, headers=HEADERS, timeout=2)
                log.info(send_req.status_code)
                send_req.raise_for_status()
            except Exception as e:
                log.error(f"[-] Error in sending data {e}")
    else:
        log.info(f"Data is not available")

        # if GL_PREV_STATUS != data[4] and payload['recipe_name']:
        #     GL_PREV_STATUS = data[4]
        #     if data[4] == 1:
        #         db.add_cycle_data(date_, payload['recipe_name'])
        #         post_api_data(date_)
        #     if data[4] == 0:
        #         db.update_stop_time(date_)
        #         post_api_data(date_)
        # else:
        #     log.info(f"Cycle is not running or recipe name is not available")


def main():
    global GL_PREV_STATUS, GL_DATA
    GL_DATA = read_plc()
    GL_PREV_STATUS = db.get_previous_status()
    date_ = datetime.today().strftime("%F")
    recipe = GL_DATA[6]
    # payload = {
    #     "air_flow_status": data[0],
    #     "door_status": data[1],
    #     "temp_high_limit": data[2],
    #     "temp_low_limit": data[3],
    #     "temp_value": data[5] / 10,
    #     "recipe_name": data[6],
    #     "target_temp": data[7]
    #
    # }

    if SEND_DATA:
        # try:
        #     log.info(f"Payload : {payload}")
        #     send_req = requests.post(URL_TELE, json=payload, headers=HEADERS, timeout=2)
        #     log.info(send_req.status_code)
        #     send_req.raise_for_status()
        # except Exception as e:
        #     log.error(f"[-] Error in sending data {e}")

        if GL_PREV_STATUS != GL_DATA[4]:
            db.update_previous_status(GL_DATA[4])
            # GL_PREV_STATUS = GL_DATA[4]
            if GL_DATA[4]:
                db.add_cycle_data(date_, recipe)
                post_api_data(date_)
            if not GL_DATA[4]:
                db.update_stop_time(date_)
                post_api_data(date_)
        else:
            log.info(f"Previous status and current status is same {GL_PREV_STATUS} || {GL_DATA[4]}")


schedule.every(30).seconds.do(post_data)
while True:
    read_all_models(GL_FIRST_TIME)
    main()
    schedule.run_pending()
    # if machine_data:
    #     post_data(machine_data)
    # else:
    #     log.info(f"Data is not available")
    GL_FIRST_TIME = False
    time.sleep(1)
