import requests
import yaml as pyyaml

# Variables
MANAGER_IP='http://0.0.0.0'
MANAGER_PORT=6000
RQ_ENDPOINT='/resourcequota/fms-tuning'
NODE_ENDPOINT='/freegpu'

def read_yaml(spec_file):
    gpu = 'nvidia.com/gpu'
    containers = None
    replicas = 1

    yaml = pyyaml.safe_load(open(spec_file))
    if yaml['kind'] == 'Pod':
        containers = yaml['spec']['containers']
    elif yaml['kind'] == 'Job':
        containers = yaml['spec']['template']['spec']['containers']

    elif yaml['kind'] == 'PyTorchJob':
        spec_base = None
        # Multi-worker case, read from worker spec
        if 'Worker' in yaml['spec']['pytorchReplicaSpecs']:
            spec_base = yaml['spec']['pytorchReplicaSpecs']['Worker']
            replicas = worker['replicas']
        else: # Read from Master spec
            spec_base = yaml['spec']['pytorchReplicaSpecs']['Master']
        containers = spec_base['template']['spec']['containers']

    if containers == None:
        raise RuntimeError("No containers in yaml")

    resources = [(int(container['resources']['requests'][gpu]), int(container['resources']['limits'][gpu])) for container in containers]
    list_reqs, list_limits = zip(*resources)
    job_resource_info = {
        "replicas": replicas,
        "request": sum(list_reqs),
        "limit": sum(list_limits)
    }
    return yaml, job_resource_info

def set_yaml(yaml, allot, pod_resource_info):
    gpu = 'nvidia.com/gpu'
    if yaml['kind'] == 'Pod':
        yaml['spec']['containers'][0]['resources']['requests'][gpu] = allot
        yaml['spec']['containers'][0]['resources']['limits'][gpu] = allot
    elif yaml['kind'] == 'Job':
        yaml['spec']['template']['spec']['containers'][0]['resources']['requests'][gpu] = allot
        yaml['spec']['template']['spec']['containers'][0]['resources']['limits'][gpu] = allot
    elif yaml['kind'] == 'PyTorchJob':
        typ = 'Master'
        if 'Worker' in yaml['spec']['pytorchReplicaSpecs']:
            typ = 'Worker'
        yaml['spec']['pytorchReplicaSpecs'][typ]['template']['spec']['containers'][0]['resources']['requests'][gpu] = allot
        yaml['spec']['pytorchReplicaSpecs'][typ]['template']['spec']['containers'][0]['resources']['limits'][gpu] = allot
    if 'annotations' not in yaml['metadata']:
        yaml['metadata']['annotations'] = pod_resource_info
    else:
        yaml['metadata']['annotations'].update({k: "{}".format(v) for k,v in pod_resource_info.items()})

    return yaml

def get_free_quota():
    res = requests.get(f'{MANAGER_IP}:{MANAGER_PORT}{RQ_ENDPOINT}')
    res_data = res.json()
    free = int(res_data['limit']) - int(res_data['used'])
    print(f'Available Quota: {free}')
    return free

def get_free_per_node():
    response = requests.get(f'{MANAGER_IP}:{MANAGER_PORT}{NODE_ENDPOINT}')
    node_info = response.json()
    sorted_node_info = dict(sorted(node_info.items(), key=lambda item: item[1], reverse=True))
    return sorted_node_info
    
