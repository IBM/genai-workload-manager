"""
Goals:
1. Read k8s yaml of pod/job
2. Query monitoring component to get #free gpus and verify limit matches
3. Query monitoring component to see which node will match
4. Modify yaml if needed
5. Apply pod/job
"""

from hikaru import load_full_yaml
from kubernetes import config
from kubernetes.client import ApiClient
import requests
import fire

# Variables
MANAGER_IP='http://0.0.0.0'
MANAGER_PORT=6000
RQ_ENDPOINT='/resourcequota/fms-tuning'
NODE_ENDPOINT='/freegpu'

def allot_gpu(spec_file):
    # 0. Connect to the k8s client
    config.load_kube_config()
    client = ApiClient()

    # 1. Read yaml of pod/job and get request/limit
    yaml = load_full_yaml(stream=open(spec_file))[0]
    gpu = 'nvidia.com/gpu'
    containers = None
    print(f'Yaml kind: {yaml.kind}')
    if yaml.kind == 'Pod':
        containers = yaml.spec.containers
    elif yaml.kind == 'Job':
        containers = yaml.spec.template.spec.containers

    resources = [(int(container.resources.requests[gpu]), int(container.resources.limits[gpu])) for container in containers]
    list_reqs, list_limits = zip(*resources)
    pod_resource_info = {
        "request": sum(list_reqs),
        "limit": sum(list_limits)
    }
    print(f'Request: {pod_resource_info["request"]} - {pod_resource_info["limit"]}')

    # 2. Get free resources as per quota
    res = requests.get(f'{MANAGER_IP}:{MANAGER_PORT}{RQ_ENDPOINT}')
    res_data = res.json()
    free = int(res_data['limit']) - int(res_data['used'])
    print(f'Available Quota: {free}')

    # 3. Get free resources per node
    response = requests.get(f'{MANAGER_IP}:{MANAGER_PORT}{NODE_ENDPOINT}')
    node_info = response.json()
    sorted_node_info = dict(sorted(node_info.items(), key=lambda item: item[1]))
    filtered_nodes = {k:v for k,v in sorted_node_info.items() if v > pod_resource_info["request"]}
    print(f'Num acceptable nodes: {len(filtered_nodes)}/{len(sorted_node_info)}')

    # 4.1 Get min(node, limit, free) 
    allot = min(*filtered_nodes.values(), pod_resource_info["limit"], free)
    #print(f'Alloted GPUs: {allot}')

    # 4.2 Choose node with closest match to allot
    # node = None
    # for (node_name, free_gpus) in filtered_nodes:
    #     if free_gpus >= allot:
    #         node = node_name

    # 4.3 Edit pod with request set to allot
    remaining = allot
    # for i, container in enumerate(pod.spec.containers):
    #     diff = container.resources.limits[gpu] - container.resources.requests[gpu]
    if yaml.kind == 'pod':
        yaml.spec.containers[0].resources.requests[gpu] = allot
        yaml.spec.containers[0].resources.limits[gpu] = allot
    elif yaml.kind == 'job':
        yaml.spec.template.spec.containers[0].resources.requests[gpu] = allot
        yaml.spec.template.spec.containers[0].resources.limits[gpu] = allot

    print(f'Alloted GPUs: {allot}')

    # 5.1 Annotate pod with request and limit
    yaml.metadata.annotations.update({k: "{}".format(v) for k,v in pod_resource_info.items()})

    # 5.2 Deploy pod
    #pod.createNamespacedPod(namespace='fms-tuning')

    #pod.deleteNamespaced

if __name__ == "__main__":
    fire.Fire(allot_gpu)
    #allot_gpu('sample-pod.yaml')
