import requests
import yaml as pyyaml

# Variables
MANAGER_IP='http://0.0.0.0'
MANAGER_PORT=6000
RQ_ENDPOINT='/resourcequota/fms-tuning'
NODE_ENDPOINT='/freegpu'

"""
====================================================================
=================== yaml parsing related helpers ===================
====================================================================
"""
def parse_yaml(yaml_input):
    yaml = None
    if isinstance(yaml_input, str):
        # File, so read it
        yaml = pyyaml.safe_load(open(yaml_input))
    elif isinstance(yaml_input, dict):
        yaml = yaml_input
    else:
        raise RuntimeError("Incorrect input, either give filename or dict")
        
    gpu = 'nvidia.com/gpu'
    containers = None
    replicas = 1

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

def set_yaml(yaml, allot):
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

    return yaml

def annotate_yaml(yaml, pod_resource_info):
    if 'annotations' not in yaml['metadata']:
        yaml['metadata']['annotations'] = pod_resource_info
    else:
        yaml['metadata']['annotations'].update({k: "{}".format(v) for k,v in pod_resource_info.items()})

    return yaml

"""
====================================================================
==================== monitoring related helpers ====================
====================================================================
"""
def get_resource_stats(request):
    free = get_free_quota()
    sorted_node_info = get_free_per_node()
    filtered_nodes = {k:v for k,v in sorted_node_info.items() if v > request}
    print(f'Num acceptable nodes: {len(filtered_nodes)}/{len(sorted_node_info)}')
    return free, sorted_node_info, filtered_nodes

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


"""
====================================================================
====================== k8s API related helpers =====================
====================================================================
"""
from kubernetes.client import CustomObjectsApi
GROUP="kubeflow.org"
VERSION="v1"
NAMESPACE="fms-tuning"
PLURAL="pytorchjobs"

def deploy_yaml(client, yaml):
    if yaml['kind'] == 'PyTorchJob':
        customObjectApi = CustomObjectsApi(client)
        api_version = yaml['apiVersion']
        group = api_version[0: api_version.find('/')]
        version = api_version[api_version.find('/') + 1:]
        plural = yaml['kind'].lower() + 's'
        customObjectApi.create_namespaced_custom_object(group, version, 'fms-tuning', plural, yaml)
    else:
        utils.create_from_yaml(client, yaml_objects = [yaml], namespace='fms-tuning')

def kill_job(client, name):
    customObjectApi = CustomObjectsApi(client)
    customObjectApi.delete_namespaced_custom_object(group=GROUP, version=VERSION, plural=PLURAL, namespace=NAMESPACE, name=name)

def edit_yaml_resources(client, job_name, allot):
    patch_body = {"spec":{"pytorchReplicaSpecs":{"Master": {"template":{"spec":{"containers":[{"name":"pytorch","resources":{"requests":{"nvidia.com/gpu":allot,},"limits":{"nvidia.com/gpu":allot }}}]}}}}}}
    return patch_yaml(client, job_name, patch_body)

def patch_yaml(client, name, patch_body):
    customObjectApi = CustomObjectsApi(client)
    return customObjectApi.patch_namespaced_custom_object(group=GROUP, version=VERSION, plural=PLURAL, namespace=NAMESPACE, name=name, body=patch_body)

def get_info_from_annotations(client, name):
    customObjectApi = CustomObjectsApi(client)
    job = customObjectApi.get_namespaced_custom_object(group=GROUP, version=VERSION, namespace=NAMESPACE, plural=PLURAL, name=name)
    job_annotations = job['metadata']['annotations']
    pod_resource_info = dict(list(map(lambda x: (x, int(job_annotations[x])), ['replicas', 'request', 'limit'])))
    return job, pod_resource_info
