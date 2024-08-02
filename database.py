import json
import sqlite3
from datetime import datetime, timedelta
import ast
import time
from config import machine_info
# from main import log
# from conversions import get_shift
import logging

log = logging.getLogger()


class CL_DBHelper:
    def __init__(self):
        self.conn = sqlite3.connect("titan.db")
        self.c = self.conn.cursor()

        self.c.execute("""CREATE TABLE IF NOT EXISTS cycle_data(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date_ DATE,
                            start_time VARCHAR(2),
                            stop_time DATETIME,
                            machine VARCHAR(2),
                            line VARCHAR(2),
                            recipe_name VARCHAR(2),
                            operator VARCHAR(2))""")

        self.c.execute("""CREATE TABLE IF NOT EXISTS
                                        sync_data(
                                            date_ DATE,
                                            payload TEXT)
                                        """)

    def add_cycle_data(self, today, recipe_name):
        try:
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # date_ = today
            # self.c.execute("SELECT * FROM cycle_data "
            #                "WHERE date_ = ? "
            #                "ORDER BY id DESC LIMIT 1", (today,))
            # fetched_data = self.c.fetchone()
            # print(fetched_data)
            # if fetched_data is not None:
            #     id_ = fetched_data[0]
            #     print(id_)
            #     self.c.execute("""UPDATE CableData SET cable_length = ? , time_ = ? WHERE
            #                              id = ? """,
            #                    (cable_length, time_, id_))
            #     log.info(f"Successfully updated data where cable_id is {cable_id}")
            # else:
            self.c.execute(
                """INSERT INTO cycle_data(date_,start_time,machine,line,recipe_name,operator) VALUES (?,?,?,?,?,?)""",
                (today, start_time, machine_info['machine_name'], machine_info['line'], recipe_name,
                 machine_info['operator']))
            log.info(f"Successfully added cycle start data")
            self.conn.commit()
            # data = self.get_cycle_data(today)
            # return data[0]
        except Exception as e:
            log.error(f"Error in adding cycle start data : {e}")

    def get_cycle_data(self, today):
        try:
            self.c.execute("SELECT * FROM cycle_data "
                           "WHERE date_ = ? "
                           "ORDER BY id DESC LIMIT 1", (today,))
            fetched_data = self.c.fetchone()
            print(fetched_data)
            return fetched_data
        except Exception as e:
            log.error(f"Error while getting cycle data")
        # return fetched_data

    def update_stop_time(self, today):
        try:
            stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.c.execute("SELECT * FROM cycle_data "
                           "WHERE date_ = ? "
                           "ORDER BY id DESC LIMIT 1", (today,))
            fetched_data = self.c.fetchone()
            if fetched_data is not None:
                id_ = fetched_data[0]
                self.c.execute("UPDATE cycle_data SET stop_time = ? WHERE id = ? ", (stop_time, id_))
                log.info(f"Successfully update stop time")
                self.conn.commit()
        except Exception as e:
            log.error(f"Error while updating stop time")

    def get_sync_data(self):
        try:
            self.c.execute('''SELECT payload FROM sync_data''')
            data = self.c.fetchall()
            # log.info(f"Sync_data: {data}")
            if data is not None:
                return data
            else:
                return []
        except Exception as e:
            log.error(f'ERROR {e} No Sync Data available')
            return []

    def add_sync_data(self, payload):
        try:
            # self.c.execute("""SELECT * FROM sync_data
            #                WHERE date_=? """,
            #                (payload['date_'], payload['shift']))
            # data = self.c.fetchone()
            # if data:
            #     self.c.execute("""UPDATE sync_data SET payload=?
            #                    WHERE date_=? AND shift = ?""",
            #                    (json.dumps(payload), payload['date_'], payload['shift']))
            #     log.info(f"Data UPDATED into SYNC TABLE")
            #
            # else:
            self.c.execute("""
                                INSERT INTO sync_data(date_,payload)
                                VALUES (?,?)""",
                           (payload['date_'], json.dumps(payload)))
            log.info(f"Data INSERTED into SYNC TABLE")
            self.conn.commit()
        except Exception as e:
            log.error(f'ERROR {e} Sync Data not added to the database')

    def delete_sync_data(self):
        try:
            # deleting the payload where ts is less than or equal to ts
            self.c.execute("""DELETE FROM sync_data """)
            self.conn.commit()
            log.info(f"Successful, Deleted from sync_data")
        except Exception as e:
            log.error(f'Error: No sync Data to clear {e}')


# date_ = datetime.today().strftime("%F")
# print(date_)
# db = CL_DBHelper()
# db.add_cycle_data(date_, "ABC")
# time.sleep(12)
# print("before updating stop time")
# d = db.get_cycle_data(date_)
# print(d[3])
# db.update_stop_time(date_)
# time.sleep(5)
# print('after updating cycle time')
# d = db.get_cycle_data(date_)
