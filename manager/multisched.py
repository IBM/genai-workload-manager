
def alloc_multi_gpu():
    # parse and get gpu req and limit
    num_replica = 2
    req_gpu = 4
    limit_gpu = 6
    # find feasible gpus as per namespace quota
    curr_quota = 10 #to be queried
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
    node_info = {'rete-pok-ext-a100-01': 4, 'rete-pok-ext-a100-04': 2, 'rete-pok-ext-a100-05': 7, 'rete-pok-ext-a100-07': 6, 'rete-pok-ext-a100-10': 6, 'rete-pok-ext-a100-11': 1, 'rete-pok-ext-a100-14': 2, 'rete-pok-ext-a100-16': 1, 'rete-pok-ext-a100-17': 3, 'rete-pok-ext-a100-18': 2, 'rete-pok-ext-a30-01': 4, 'rete-pok-ext-a30-02': 4}
    sorted_node_info = dict(sorted(node_info.items(), key=lambda item: item[1],reverse=True))
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
       
alloc_multi_gpu()

