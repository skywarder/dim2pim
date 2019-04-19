from flask import Flask
from flask import request
import os
from flask import send_from_directory

app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/dim2pim/', methods=['GET', 'POST'])
def hello_world():
    try:
        product_id = request.args.get('pid', default = 'nan', type = str)
    except e:
        product_id = 0
    try:
        box_type = request.args.get('box', default = 'unknown', type = str)
    except e:
        box = 'unknown'
    return 'Request: product = '+product_id +"; box = "+box_type

if __name__ == "__main__":
    print(os.path.join(app.root_path, 'static'))
    app.run()