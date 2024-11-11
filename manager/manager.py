"""
Goals:
1. Read k8s yaml of pod/job
2. Query monitoring component to get #free gpus and verify limit matches
3. Query monitoring component to see which node will match
4. Modify yaml if needed
5. Apply pod/job
"""

from kubernetes import config, utils, client
from kubernetes.client import ApiClient, CustomObjectsApi
import fire
from utils import *

def setup_k8s_client():
    # 0. Connect to the k8s client
    config.load_kube_config()
    client = ApiClient()

def print_yaml(yaml):
    print(yaml)

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

def allot_single_node(spec_file):
    client = setup_k8s_client()

    # 1. Read yaml of pod/job and get request/limit
    yaml, pod_resource_info = read_yaml(spec_file)
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

    # 5.1 Set allot, annotate with request and limit 
    yaml = set_yaml(yaml, allot, pod_resource_info)

    # 5.2 Deploy yaml
    deploy_yaml(client, yaml)

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
