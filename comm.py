from pyModbusTCP.client import ModbusClient
from logger import log
from config import machine_info
import struct

IP_ADDRESS = machine_info['machine_ip']
PORT = machine_info['machine_port']
# registers data
discrete_registers = [(90, 4)]

holding_registers = [(6, 1)]
recipe = [(1300, 8)]
target_temp = [(1770, 2)]
trigger = [(10, 1)]  # to start sending temperature data

# registers data
models_registers = [(1200, 10, 610, 10, 705, 5), (1210, 10, 620, 10, 710, 5), (1220, 10, 630, 10, 715, 5),
                    (1230, 10, 640, 10, 720, 5), (1240, 10, 650, 10, 725, 5),
                    (1250, 10, 660, 10, 730, 5)]


def conn():
    try:
        client = ModbusClient(host=IP_ADDRESS, port=PORT, unit_id=1, auto_open=True, auto_close=True, timeout=2)
        log.info(f"connected with plc")
        return client
    except Exception as e:
        log.error(f"Error: {e}")
        return None


def convert_to_float(register1, register2):
    # Combine the two 16-bit registers into one 32-bit integer
    combined_value = (register1 << 16) | register2

    # Convert the 32-bit integer to a float
    float_value = struct.unpack('>f', struct.pack('>I', combined_value))[0]

    return float_value


# Function to convert an integer to a two-character string in swapped order
def int_to_two_chars_swapped(value: int):
    first_char = chr(value % 256)  # Get the second character
    second_char = chr(value // 256)  # Get the first character
    return first_char + second_char


def read_plc():
    global discrete_registers, holding_registers
    mb_client = conn()
    # log.info(mb_client)
    if mb_client:
        data = []
        try:
            # reading discrete inputs
            for bits in discrete_registers:
                status = mb_client.read_discrete_inputs(bits[0], bits[1])
                log.info(f"Status : {status}")
                data += status

            # reading temperature
            temp_trigger = mb_client.read_coils(10, 1)
            log.info(f"Temperature Trigger : {temp_trigger}")
            data += temp_trigger
            if temp_trigger[0]:
                for reg in holding_registers:
                    temp = mb_client.read_holding_registers(reg[0], reg[1])
                    log.info(f"Temperature : {temp}")
                    temp_ = temp[0] // 10
                    temp[0] = temp_
                    data += temp

                for reg in recipe:
                    recipe_data = mb_client.read_holding_registers(reg[0], reg[1])
                    log.info(f"Recipe_data : {recipe_data}")
                    result = ''.join(int_to_two_chars_swapped(value) for value in recipe_data if value != 0)
                    result = result.replace("\x00", "")
                    log.info(f"Converted Recipe : {result}")
                    data.append(result)
                    for target in target_temp:
                        target_value = mb_client.read_holding_registers(target[0], target[1])
                        target_value = convert_to_float(target_value[1], target_value[0])
                        target_value = round(target_value, 2)
                        log.info(f"Target temperature : {target_value}")
                        data.append(target_value)
            else:
                d = [0, "", 0]
                data.extend(d)

            log.info(f"Data from plc is : {data}")

            return data
        except Exception as msg:
            log.error(f"Error: {msg}")
            return []
    return []

# def read_all_models(tags):
#     mb_client = conn()
#     # log.info(mb_client)
#     temp_len = 5
#     models = []
#     if mb_client:
#         for tag in tags:
#             model_name = mb_client.read_holding_registers(tag[0], tag[1])
#             model_name = ''.join(int_to_two_chars_swapped(value) for value in model_name if value != 0)
#             model_name = model_name.replace("\x00", "")
#             durations = mb_client.read_holding_registers(tag[2], tag[3])
#             set_temperatures = mb_client.read_holding_registers(tag[4], tag[5])
#
#             stages = []
#             current_temperature = 0
#
#             for j in range(temp_len):
#                 # First add an increase stage
#                 stages.append({
#                     "start_temperature": current_temperature,
#                     "end_temperature": set_temperatures[j],
#                     "duration_minutes": durations[j]
#                 })
#                 current_temperature = set_temperatures[j]
#
#                 # Then add a hold stage
#                 if j + 1 < temp_len:
#                     stages.append({
#                         "start_temperature": current_temperature,
#                         "end_temperature": current_temperature,
#                         "duration_minutes": durations[j + 1]
#                     })
#             model_data = {
#                 "model": model_name,
#                 "stages": stages
#             }
#
#             models.append(model_data)
#
#             return models
