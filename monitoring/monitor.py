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
SECRET_FILE = 'secret.json'

@app.route('/freegpu', methods=['GET'])
def getfreegpu():
    headers = json.load(open('secret.json'))
    response = requests.get('https://prometheus-k8s-openshift-monitoring.apps.pok.res.ibm.com/api/v1/query?query=group%20by(Hostname,gpu,exported_pod)(DCGM_FI_PROF_GR_ENGINE_ACTIVE)', headers=headers)
    '''
    with open("output.json", 'r') as f:
            data = json.load(f)
    '''
    data = response.json()
    free_gpu_list = {}
    
    temp_data = data["data"]["result"]
    for itr in range(len(temp_data)):
       if "exported_pod" not in temp_data[itr]["metric"]:
               if temp_data[itr]["metric"]["Hostname"] not in free_gpu_list:
                     #gpu_list[temp_data[itr]["metric"]["Hostname"]] = []
                     free_gpu_list[temp_data[itr]["metric"]["Hostname"]] = 0
               #gpu_list[temp_data[itr]["metric"]["Hostname"]].append(temp_data[itr]["metric"]["gpu"])
               free_gpu_list[temp_data[itr]["metric"]["Hostname"]] += 1
    return jsonify(free_gpu_list), 200
@app.route('/resourcequota/<ns>', methods=['GET'])
def getresourcequota(ns):
    print(f'{ns}')
    ns = f'{ns}'
    config.load_kube_config()   
    v1 = client.CoreV1Api()
    hard = v1.list_namespaced_resource_quota(ns).items[0].status.hard['requests.nvidia.com/gpu']
    used = v1.list_namespaced_resource_quota(ns).items[0].status.used['requests.nvidia.com/gpu']
    quota = {'limit':hard,'used':used}
    
    #gpu_limit = qu['items'][0]['spec']['hard']['requests.nvidia.com/gpu']
    #print(qu)
    return jsonify(quota), 200
if __name__ == '__main__':
    app.run(host=f"{HOST}", port=f"{PORT}", debug=True)
