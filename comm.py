from pyModbusTCP.client import ModbusClient
from logger import log
from config import machine_info

IP_ADDRESS = machine_info['machine_ip']
PORT = machine_info['machine_port']

# registers data
discrete_registers = [(90, 4)]
holding_registers = [(6, 1)]
recipe = [(1000, 8)]
target_temp = [(458, 1)]
trigger = [(10, 1)]  # to start sending temperature data


def conn():
    try:
        client = ModbusClient(host=IP_ADDRESS, port=PORT, unit_id=1, auto_open=True, auto_close=True, timeout=2)
        log.info(f"connected with plc")
        return client
    except Exception as e:
        log.error(f"Error: {e}")
        return None


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
                    data += temp

                for reg in recipe:
                    recipe_data = mb_client.read_holding_registers(reg[0], reg[1])
                    log.info(f"Recipe_data : {recipe_data}")

                    # Given data
                    # data = [21575, 18247, 17753, 19029, 18246, 0, 0, 0]

                    # Convert each non-zero integer to a two-character string (swapped order) and concatenate the
                    # results
                    result = ''.join(int_to_two_chars_swapped(value) for value in recipe_data if value != 0)

                    # print(result)  # Should output "GTGGYEUJFG"
                    log.info(f"Converted Recipe : {result}")
                    data.append(result)
                    for target in target_temp:
                        target_value = mb_client.read_holding_registers(target[0], target[1])
                        log.info(f"Target temperature : {target_value}")
                        data.append(target_value[0])
                # log.info(f"Data from plc is : {data}")
            else:
                d = [0, "", 0]
                data.extend(d)

            log.info(f"Data from plc is : {data}")

            return data
        except Exception as msg:
            log.error(f"Error: {msg}")
            return []
    return []
