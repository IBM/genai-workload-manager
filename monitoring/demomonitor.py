import json
import os
import yaml
from flask import Flask, jsonify, request, abort
import requests
from kubernetes import client, config
app = Flask(__name__)
'''
def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

config_file = os.environ.get('CONFIG_FILE')
if config_file:
    app.config.update(load_config(config_file))

'''
HOST=os.environ.get('MHOST','0.0.0.0')
PORT=os.environ.get('MPORT',6000)

@app.route('/freegpu', methods=['GET'])
def getfreegpu():
    with open("sample_json/output.json", 'r') as f:
            data = json.load(f)
   
    print(data)    
    return jsonify(data), 200

@app.route('/resourcequota/<ns>', methods=['GET'])
def getresourcequota(ns):
    print(f'{ns}')
    ns = f'{ns}'
    try:
        config.load_kube_config()   
    except Exception as e:
        config.load_incluster_config()
    v1 = client.CoreV1Api()
    hard = v1.list_namespaced_resource_quota(ns).items[0].status.hard['requests.nvidia.com/gpu']
    used = v1.list_namespaced_resource_quota(ns).items[0].status.used['requests.nvidia.com/gpu']
    quota = {'limit':hard,'used':used}
    
    #gpu_limit = qu['items'][0]['spec']['hard']['requests.nvidia.com/gpu']
    #print(qu)
    return jsonify(quota), 200
if __name__ == '__main__':
    app.run(host=f"{HOST}", port=f"{PORT}", debug=True)
