import time
from pprint import pprint
from pyModbusTCP.client import ModbusClient
from logger import log
import requests
# from logger import log
from config import machine_info

IP_ADDRESS = "192.168.0.50"
PORT = 502

# registers data
models_registers = [(1200, 10, 600, 10, 700, 5), (1210, 10, 610, 10, 705, 5), (1220, 10, 620, 10, 710, 5),
                    (1230, 10, 630, 10, 715, 5), (1240, 10, 640, 10, 720, 5),
                    (1250, 10, 650, 10, 725, 5)]

GL_MODEL_SAVE = False
ACCESS_TOKEN = machine_info["access_token"]
HOST_API = machine_info["host_api"]
URL_API = f'http://{HOST_API}/recipe_master/'
HEADERS = {"Content-Type": "application/json"}


def conn():
    try:
        client = ModbusClient(host=IP_ADDRESS, port=PORT, unit_id=1, auto_open=True, auto_close=True, timeout=2)
        log.info(f"connected with plc")
        return client
    except Exception as e:
        log.info(f"Error: {e}")
        return None


# Function to convert an integer to a two-character string in swapped order
def int_to_two_chars_swapped(value: int):
    first_char = chr(value % 256)  # Get the second character
    second_char = chr(value // 256)  # Get the first character
    return first_char + second_char


# def read_plc():
#     global discrete_registers, holding_registers
#     mb_client = conn()
#     # print(mb_client)
#     if mb_client:
#         data = []
#         try:
#             # reading discrete inputs
#             for bits in discrete_registers:
#                 status = mb_client.read_discrete_inputs(bits[0], bits[1])
#                 print(f"Status : {status}")
#                 data += status
#
#             # reading temperature
#             temp_trigger = mb_client.read_coils(10, 1)
#             print(f"Temperature Trigger : {temp_trigger}")
#             data += temp_trigger
#             if temp_trigger[0]:
#                 for reg in holding_registers:
#                     temp = mb_client.read_holding_registers(reg[0], reg[1])
#                     print(f"Temperature : {temp}")
#                     temp_ = temp[0] // 10
#                     temp[0] = temp_
#                     data += temp
#
#                 for reg in recipe:
#                     recipe_data = mb_client.read_holding_registers(reg[0], reg[1])
#                     print(f"Recipe_data : {recipe_data}")
#                     result = ''.join(int_to_two_chars_swapped(value) for value in recipe_data if value != 0)
#                     result = result.replace("\x00", "")
#                     print(f"Converted Recipe : {result}")
#                     data.append(result)
#                     for target in target_temp:
#                         target_value = mb_client.read_holding_registers(target[0], target[1])
#                         print(f"Target temperature : {target_value}")
#                         data.append(target_value[0])
#             else:
#                 d = [0, "", 0]
#                 data.extend(d)
#
#             print(f"Data from plc is : {data}")
#
#             return data
#         except Exception as msg:
#             print(f"Error: {msg}")
#             return []
#     return []

def read_data(models):
    mb_client = conn()
    temp_len = 5
    payload = {}
    all_models = []
    for tag in models:
        model_name = mb_client.read_holding_registers(tag[0], tag[1])
        model_name = ''.join(int_to_two_chars_swapped(value) for value in model_name if value != 0)
        model_name = model_name.replace("\x00", "")
        durations = mb_client.read_holding_registers(tag[2], tag[3])
        set_temperatures = mb_client.read_holding_registers(tag[4], tag[5])

        # print(f"""model_name : {model_name}
        #           durations  : {durations}
        #           set_temp   : {set_temperatures}""")
        # print("#" * 20)
        if model_name:
            stages = []
            current_temperature = 30
            duration_index = 0
            for j in range(temp_len):
                # print(f"duration index : {duration_index}")
                # First add an increase stage
                stages.append({
                    "duration_mins": durations[duration_index],
                    "stop_temp": set_temperatures[j],
                    "start_temp": current_temperature,
                })
                # print(f"Stages 1 : {stages}")
                current_temperature = set_temperatures[j]

                # Then add a hold stage
                if j + 1 <= temp_len:
                    stages.append({
                        "duration_mins": durations[duration_index + 1],
                        "stop_temp": current_temperature,
                        "start_temp": current_temperature,
                    })
                # print(f"Stages 2 : {stages}")
                duration_index += 2
            model_data = {
                "recipe_name": model_name,
                "stages": stages
            }

            all_models.append(model_data)
            payload["recipes"] = all_models
    return payload


def read_all_models(first_time_status: bool):
    global GL_MODEL_SAVE, models_registers
    try:
        mb_client = conn()
        # print(mb_client)
        if mb_client:
            model_trigger = mb_client.read_holding_registers(233, 1)

            if not model_trigger[0]:
                GL_MODEL_SAVE = False
            log.info(f"Model trigger is {model_trigger} and GL_MODEL_SAVE is {GL_MODEL_SAVE}")
            if model_trigger[0] and not GL_MODEL_SAVE:
                GL_MODEL_SAVE = True
                payload = read_data(models_registers)
                if payload:
                    post_data(payload)
            if GL_MODEL_SAVE:
                reset_trigger = mb_client.write_single_register(233, 0)
                log.info("Trigger reset")
            if first_time_status:
                log.info(f"read all models because code was restarted")
                payload = read_data(models_registers)
                post_data(payload)
    except Exception as e:
        log.error(f"Error while reading models : {e}")


def post_data(payload: dict):
    try:
        log.info(f"Sending all models : {payload}")
        send_req = requests.post(URL_API, json=payload, headers=HEADERS, timeout=2)
        log.info(send_req.status_code)
        send_req.raise_for_status()
    except Exception as e:
        log.error(f"[-] Error in sending data {e}")

# while True:
#     models = read_all_models(models_registers)
#     pprint(models)
#     time.sleep(1)
