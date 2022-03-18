from prometheus_client import Gauge,start_http_server
from time import sleep
import os
import pycurl
from io import BytesIO
from urllib.parse import urlencode
import threading
import yaml

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, 'config.yml')) as conf_file:
    database_list = yaml.full_load(conf_file)

with open(os.path.join(__location__, '.credentials')) as creds_file:
    credentials = creds_file.read().strip()
    credentials = credentials.split(":")

table_number_rows = Gauge(
    "table_number_rows",
    "Number of rows in the requested table",
    ['table_name','shard_number', 'replica_name']
    )



def curl_request(url, auth, params):
    params = {f'{params[0]}': f'{params[1]}'}
    buffer_curl = BytesIO()
    application_curl = pycurl.Curl()
    application_curl.setopt(application_curl.URL, url + '?' + urlencode(params))
    application_curl.setopt(application_curl.USERPWD, f'{auth[0]}:{auth[1]}')
    application_curl.setopt(application_curl.WRITEDATA, buffer_curl)
    application_curl.perform()
    application_curl.close()
    get_body = buffer_curl.getvalue()
    return(get_body.decode('utf8'))



def gauge_metric(value, table, shard_number, replica_name):
    if type(value) != int and not value.isdigit():
        raise Exception('Only integer, please!')
    else:
        int(value)

    table_number_rows.labels(
        f'{table}',
        f'{shard_number}',
        f'{replica_name}').set(value)



# Управление потоком, выполнять curl url каждые 15 секунд
def gauge_threads(replica, auth, database, table):
    while True:
        shard_number = replica[2]
        replica_name = replica[0]
        replica_port = replica[1]

        row_value = curl_request(
               f'http://{replica_name}:{replica_port}/',
                auth,
                ("query", f"""
                SELECT log_max_index FROM system.replicas
                WHERE (database = '{database}' and table = '{table}')
                FORMAT Vertical
                """ )
                )

        finish_value = int(row_value.split(":")[-1].strip())

        t = threading.Thread(target=gauge_metric,args=(
            finish_value,
            table,
            shard_number,
            replica_name))
        t.setDaemon(True)
        t.start()
        sleep(15)



if __name__ == '__main__':
    start_http_server(9091)
    threads = []

    for db_name, db in database_list.items():
        for table_name, table in db.items():
            for shard_id, shard in table.items():
                for replica in shard:
                    replica = replica.split(":")
                    replica.append(shard_id)
                    t = threading.Thread(target=gauge_threads,args=(
                        replica, credentials, db_name, table_name))
                    threads.append(t)

    for thread in threads:
        thread.setDaemon(True)
        thread.start()
    thread.join()
