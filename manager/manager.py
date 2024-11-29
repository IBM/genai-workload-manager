"""
Goals:
1. Read k8s yaml of pod/job
2. Query monitoring component to get #free gpus and verify limit matches
3. Query monitoring component to see which node will match
4. Modify yaml if needed
5. Apply pod/job
"""

from kubernetes import config, utils, client
from utils import *

def setup_k8s_client(standalone):
    # 0. Connect to the k8s client
    if standalone:
        config.load_kube_config()
        return client.ApiClient()
    else:
        return client.ApiClient(configuration=config.load_incluster_config())

def print_yaml(yaml):
    print(yaml)

def deploy(filename, standalone=False):
    client = setup_k8s_client(standalone)

    # 1. Read yaml of pod/job and get request/limit
    yaml, pod_resource_info = parse_yaml(filename)
    print(f'Request: {pod_resource_info["request"]} - {pod_resource_info["limit"]}')

    # 2. Get quota and node free resources
    free, sorted_node_info, filtered_nodes = get_resource_stats(pod_resource_info["request"])

    # 3.1 Check if multi-replica, then call alloc_multi_gpu
    if pod_resource_info["replicas"] != 1:
        alloc_multi_gpu(pod_resource_info, free, sorted_node_info)

    # 3.2 Get allot = min(node, limit, free) 
    allot = min(*filtered_nodes.values(), pod_resource_info["limit"], free)
    print(f'Alloted GPUs: {allot}')

    # 4.1 Set allot, annotate with request and limit 
    yaml = set_yaml(yaml, allot)
    yaml = annotate_yaml(yaml, pod_resource_info)

    # 4.2 Deploy yaml
    deploy_yaml(client, yaml)
    name = yaml['metadata']['name']
    print(f"Deployed resource: {name}")

    # 5. Inform job manager
    add_job(name, pod_resource_info, allot)

def scale(name):
    client = setup_k8s_client()

    # 0. Decide which job to scale
    job_name = name if name is not None else job_to_scale()
    if job_name == None:
        print("No jobs to scale")
        return
    
    print(f'Scaling pytorchjob: {job_name}')

    # 1.1 Use annotations to get job request/limit
    yaml, pod_resource_info = get_info_from_annotations(client, job_name)

    # 1.2 Get GPU assignment of this job from yaml
    _, assn = parse_yaml(yaml)
    assigned_gpus = assn['request']
    print(f'Request: {pod_resource_info["request"]} - {pod_resource_info["limit"]}, Alloted: {assigned_gpus}')

    # 2.0 Get quota and node free resources
    free, sorted_node_info, filtered_nodes = get_resource_stats(pod_resource_info["request"])

    podlist = get_pod_by_selector(client, job_name)
    # 2.1 Find pod(s) associated and get node(s) assigned
    if len(podlist.items) != 0:
        pod = podlist.items[0]

        # 2.2 Count current assignment as free
        free += assigned_gpus
        #node_name = pod['node_name']

    # 3.1 TODO: Add multi-gpu later

    # 3.2 Allot new gpus
    allot = min(*filtered_nodes.values(), pod_resource_info["limit"], free)
    print(f'New allotment: {allot}')

    if allot != assigned_gpus:
        # 4.1 Edit resource, limit and command and deploy
        print("Patching object with new resource allotment")
        yaml = patch_job_resources(client, job_name, allot)
        old_command = get_nested_value(yaml, 'spec.pytorchReplicaSpecs.Master.template.spec.containers.0.command')
        new_command = [ x.replace(f'--num_processes={assigned_gpus}', f'--num_processes={allot}') for x in old_command]
        patch_job_command(client, job_name, new_command)

        # 4.2 Delete pod to respawn automatically
        if len(podlist.items) != 0:
            pod_name = podlist.items[0].metadata.name
            kill_pod(client, pod_name)
    else:
        print("No changes to resource, doing nothing...")

def alloc_multi_gpu(pod_resource_info, curr_quota, sorted_node_info):
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

    # TODO: add deployment logic later
