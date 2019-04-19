# -*- coding: utf-8 -*-
"""Wait for the CSV file updates and import data to PIM."""
from flask import Flask
from flask import request
from flask import url_for
import pandas
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
# Reduce the amount of logs:
import logging
import os
from flask import send_from_directory
logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

# import Akeneo API Client
try:
    from akeneo import AkeneoAPI
except ModuleNotFoundError as e:
    print ("SmartPIM API wrapper for python is not installed")

# ************* НАСТРОЙКИ ****************
# -------  PIM -----------
akeneo = AkeneoAPI(
    url="http://pim.brandmaker-russia.com/",
    client_id="1_18ikqygsu6jos4kog4g8o8o000kwwgcs0w04sw80cs08gw04kg",
    secret="2a6kqz5rscg0gcg0w40c8w0okwg08cwcwkc4ck8k0wg8wc0sk0",
    username="dim_machine",
    password="123@qwe",
    verbose=False
)
# ------- PIM fields mapping ----------
# TODO
# OUTER
# INNER
# UNIT
# ------- Dimensions file -------------
DIM_FILE_PATH = 'C:\ML\Dim2pim\PBM0000data.csv'
DIM_FILE_CHECK_INTERVAL = 10 # seconds
DIM_FILE_DELIMITER = ';'
DIM_TIMESTAMP_COLUMN = 21 # starts with 0 (zero)
DIM_DEPTH_COLUMN = 13
DIM_WIDTH_COLUMN = 14
DIM_HEIGHT_COLUMN = 15
DIM_WEIGHT_COLUMN = 19
DIM_BARCODE_COLUMN= 0
DIM_BARCODE_UNIT_COLUMN=0
DIM_QTY_COLUMN = 4
# ------- Google sheets logging
GS_LOG_USERNAME = ''
GS_LOG_PASSWORD = ''
GS_LOG_BASE_URL = ''
# ************* ********* ****************

# ---------- Global variables -----------
product_id = 'nan'
box_type = 'unknown'
# ----- prepare web server routing
app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Example: http://localhost:5000/dim2pim/?pid=10004&box=outer
@app.route('/dim2pim/', methods=['GET', 'POST'])
def set_pid_boxtype():
    global product_id
    global box_type
    try:
        product_id = request.args.get('pid', default = 'nan', type = str)
    except e:
        product_id = 'nan'
    try:
        box_type = request.args.get('box', default = 'unknown', type = str)
    except e:
        box_type = 'unknown'
    logging.debug('Request: product = '+product_id +"; box = "+box_type)
    return 'Request: product = '+product_id +"; box = "+box_type
# ----------------------------------

class CSVFileHandler(FileSystemEventHandler):
    
    def __init__(self, _dim_reader):
        super(FileSystemEventHandler, self).__init__()
        self.dim_reader = _dim_reader

    def on_modified(self, event):
        if not event.is_directory and not 'thumbnail' in event.src_path:
            logging.debug("Updated: " + event.src_path)
            self.dim_reader.get_new_line()

class Dim_reader():
    last_line_time = 0
    
    def __init__(self, _pim_saver):
        self.last_line_time = 0
        self.pim_saver = _pim_saver
        
    def wait_for_updates(self):
        event_handler = CSVFileHandler(self)
        observer = Observer()
        observer.schedule(event_handler, os.path.dirname(DIM_FILE_PATH), recursive=False)
        observer.start()
        logging.debug("Watchdog observer started")
        try:
        #    while True:
        #        time.sleep(DIM_FILE_CHECK_INTERVAL)
        #        logging.debug("Check for the updates...")
        
            if __name__ == "__main__":
                app.run()
        except KeyboardInterrupt:
            observer.stop()
            sys.exit()
        observer.join()

    def get_new_line(self):
        try:
            data_src = pandas.read_csv(DIM_FILE_PATH, delimiter=DIM_FILE_DELIMITER, decimal=',', encoding='ISO-8859-1')
        except Exception as e:
            logging.error('Error while reading CSV file: {name}...:\n{error}\n'.format(
                name=DIM_FILE_PATH, error=e))
            raise e
        if not data_src.empty and not data_src.tail(1).empty:
            row = data_src.tail(1).values[0]
        else:
            return 
        
        if (self.last_line_time) < row[DIM_TIMESTAMP_COLUMN]:
            self.last_line_time = row[DIM_TIMESTAMP_COLUMN]
            self.pim_saver.save_to_PIM(row)
        
class PIM_saver():
    def __init__(self):
        self.last_line_time = 0
    
    def save_to_PIM(self, _new_line):
        logging.debug('Requested: product = '+product_id +"; box = "+box_type)
        logging.debug(_new_line)
        if product_id == 'nan':
            logging.info('Product_ID is undefined. Cannot save to PIM. Skipping.')
            return
        if box_type == 'outer':
            self.save_to_OUTER(_new_line)
        elif box_type == 'inner':
            self.save_to_INNER(_new_line)
        elif box_type == 'unit':
            self.save_to_UNIT(_new_line)
        else:
            logging.info('Box type is undefined. Cannot save to PIM. Skipping.')
        
    def save_to_INNER(self, _new_line):
        try:
            update_data = [{ "identifier": product_id, "values": { "inner_pack_qty": [ { "locale": None, "scope": None,                                 "data": int(_new_line[DIM_QTY_COLUMN]) } ], "gtin_inner_pack": [ { "locale": None, "scope": None, "data": str(_new_line[DIM_BARCODE_COLUMN]) } ], "inner_pack_depth": [ { "locale": None, "scope": None, "data": { "amount": float(_new_line[DIM_DEPTH_COLUMN])/10, "unit": "CENTIMETER" } } ], "inner_pack_width": [ { "locale": None, "scope": None, "data": { "amount": float(_new_line[DIM_WIDTH_COLUMN])/10, "unit": "CENTIMETER" } } ], "inner_pack_height": [ { "locale": None, "scope": None, "data": { "amount": float(_new_line[DIM_HEIGHT_COLUMN])/10, "unit": "CENTIMETER" } } ], "inner_pack_weight": [ { "locale": None, "scope": None, "data": { "amount": float(_new_line[DIM_WEIGHT_COLUMN])/1000, "unit": "KILOGRAM" } } ] } }]
            update_product = akeneo.patch('products', update_data)
            akeneo.log.info(update_product)
            akeneo.close_session()
        except Exception as e:
            logging.error('Cannot update product: {pid}...:\n{error}\n'.format(
                pid=product_id, error=e))
            
    def save_to_OUTER(self, _new_line):
        try:
            update_data = [{ "identifier": product_id, "values": { "units_per_pack": [ { "locale": None, "scope": None,                                 "data": int(_new_line[DIM_QTY_COLUMN]) } ], "gtin_outer_pack": [ { "locale": None, "scope": None, "data": str(_new_line[DIM_BARCODE_COLUMN]) } ], "pack_depth": [ { "locale": None, "scope": None, "data": { "amount": float(_new_line[DIM_DEPTH_COLUMN])/10, "unit": "CENTIMETER" } } ], "pack_width": [ { "locale": None, "scope": None, "data": { "amount": float(_new_line[DIM_WIDTH_COLUMN])/10, "unit": "CENTIMETER" } } ], "pack_height": [ { "locale": None, "scope": None, "data": { "amount": float(_new_line[DIM_HEIGHT_COLUMN])/10, "unit": "CENTIMETER" } } ], "pack_gross_weight": [ { "locale": None, "scope": None, "data": { "amount": float(_new_line[DIM_WEIGHT_COLUMN])/1000, "unit": "KILOGRAM" } } ] } }]
            update_product = akeneo.patch('products', update_data)
            akeneo.log.info(update_product)
            akeneo.close_session()
        except Exception as e:
            logging.error('Cannot update product: {pid}...:\n{error}\n'.format(
                pid=product_id, error=e))
            
    def save_to_UNIT(self, _new_line):
        try:
            update_data = [{ "identifier": product_id, "values": { "ean": [ { "locale": None, "scope": None, "data": str(_new_line[DIM_BARCODE_COLUMN]) } ], "depth": [ { "locale": None, "scope": None, "data": { "amount": float(_new_line[DIM_DEPTH_COLUMN])/10, "unit": "CENTIMETER" } } ], "width": [ { "locale": None, "scope": None, "data": { "amount": float(_new_line[DIM_WIDTH_COLUMN])/10, "unit": "CENTIMETER" } } ], "height": [ { "locale": None, "scope": None, "data": { "amount": float(_new_line[DIM_HEIGHT_COLUMN])/10, "unit": "CENTIMETER" } } ], "gross_weight": [ { "locale": None, "scope": None, "data": { "amount": float(_new_line[DIM_WEIGHT_COLUMN]/1000), "unit": "KILOGRAM" } } ] } }]
            update_product = akeneo.patch('products', update_data)
            akeneo.log.info(update_product)
            akeneo.close_session()
        except Exception as e:
            logging.error('Cannot update product: {pid}...:\n{error}\n'.format(
                pid=product_id, error=e))
        
pim_saver = PIM_saver()
dim_reader = Dim_reader(pim_saver)
dim_reader.wait_for_updates()
    



        
    









# ---------------------------------------------------