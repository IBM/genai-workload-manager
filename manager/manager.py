"""
Goals:
1. Read k8s yaml of pod/job
2. Query monitoring component to get #free gpus and verify limit matches
3. Query monitoring component to see which node will match
4. Modify yaml if needed
5. Apply pod/job
"""

from hikaru import load_full_yaml
import yaml
from kubernetes import config
from kubernetes.client import ApiClient
import requests
import fire

# Variables
MANAGER_IP='http://0.0.0.0'
MANAGER_PORT=6000
RQ_ENDPOINT='/resourcequota/fms-tuning'
NODE_ENDPOINT='/freegpu'

def setup_k8s_client():
    # 0. Connect to the k8s client
    config.load_kube_config()
    client = ApiClient()

def read_pod_job_yaml(spec_file):
    gpu = 'nvidia.com/gpu'
    containers = None
    yaml = load_full_yaml(stream=open(spec_file))[0]
    print(f'Yaml kind: {yaml.kind}')
    if yaml.kind == 'Pod':
        containers = yaml.spec.containers
    elif yaml.kind == 'Job':
        containers = yaml.spec.template.spec.containers
    resources = [(int(container.resources.requests[gpu]), int(container.resources.limits[gpu])) for container in containers]
    list_reqs, list_limits = zip(*resources)
    pod_resource_info = {
        "replicas": 1,
        "request": sum(list_reqs),
        "limit": sum(list_limits)
    }
    return yaml, pod_resource_info

def read_pytorch_yaml(spec_file):
    print(f"Yaml kind: {yaml['kind']}")
    yaml = yaml.safe_load(open(spec_file))
    gpu = 'nvidia.com/gpu'
    if yaml['kind'] == 'PyTorchJob':
        master = yaml['spec']['pytorchReplicaSpecs']['Master']
        replicas = master['replicas']
        containers = master['template']['spec']['containers']
        resources = [(int(container['resources']['requests'][gpu]), int(container['resources']['limits'][gpu])) for container in containers]
        list_reqs, list_limits = zip(*resources)
        pod_resource_info = {
            "replicas": replicas,
            "request": sum(list_reqs),
            "limit": sum(list_limits)
        }
        return pod_resource_info
    
def set_pod_job_yaml(yaml, allot, pod_resource_info):
    if yaml.kind == 'pod':
        yaml.spec.containers[0].resources.requests[gpu] = allot
        yaml.spec.containers[0].resources.limits[gpu] = allot
    elif yaml.kind == 'job':
        yaml.spec.template.spec.containers[0].resources.requests[gpu] = allot
        yaml.spec.template.spec.containers[0].resources.limits[gpu] = allot

    yaml.metadata.annotations.update({k: "{}".format(v) for k,v in pod_resource_info.items()})
    #yaml.createNamespacedPod(namespace='fms-tuning')
    #yaml.deleteNamespaced
    
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
    
def allot_single_node(spec_file):
    client = setup_k8s_client()

    # 1. Read yaml of pod/job and get request/limit
    yaml, pod_resource_info = read_pod_job_yaml(spec_file)
    print(f'Request: {pod_resource_info["request"]} - {pod_resource_info["limit"]}')

    # 2. Get free resources as per quota
    free = get_free_quota()

    # 3. Get free resources per node
    sorted_node_info = get_free_per_node()
    filtered_nodes = {k:v for k,v in sorted_node_info.items() if v > pod_resource_info["request"]}
    print(f'Num acceptable nodes: {len(filtered_nodes)}/{len(sorted_node_info)}')

    # 4.1 Get min(node, limit, free) 
    allot = min(*filtered_nodes.values(), pod_resource_info["limit"], free)

    print(f'Alloted GPUs: {allot}')

    # 5. Set allot, annotate with request and limit and deploy
    set_pod_job_yaml(yaml, allot, pod_resource_info)

def alloc_multi_gpu(spec_file):
    client = setup_k8s_client()
    # parse and get gpu req and limit
    pod_resource_info = read_pytorch_yaml(spec_file)
    num_replica, req_gpu, limit_gpu = pod_resource_info["replicas"], pod_resource_info["request"], pod_resource_info["limit"]

    # find feasible gpus as per namespace quota
    curr_quota = get_free_quota()
    total_req_gpu = num_replica * req_gpu
    total_limit_gpu = num_replica * limit_gpu
    if total_req_gpu <= curr_quota & curr_quota <= total_limit_gpu:
        new_req_gpu = curr_quota
    elif curr_quota < total_req_gpu:
        new_req_gpu = curr_quota 
    else:
        new_req_gpu = total_limit_gpu
    print(new_req_gpu)
    
    # find for the above feasible gpus no.of gpus per pod in the job
    sorted_node_info = get_free_per_node()
    print(sorted_node_info)
    print(len(sorted_node_info))
    j = new_req_gpu
    per_pod = new_req_gpu/num_replica
    r = num_replica
    for node in sorted_node_info:
         if j/sorted_node_info[node] <=1:
             r = 0
             j = 0
             break
         else:
             inst = sorted_node_info[node]/per_pod
             if inst > 1:
                 r = r - inst
                 j = j - (inst*per_pod)
    if j>0:
       print("cannot allocate")
    else:
       print("can allocate")

if __name__ == "__main__":
    fire.Fire(allot_single_node)
    #allot_gpu('sample-pod.yaml')
