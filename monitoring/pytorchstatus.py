from kubernetes import client, config,watch
import time
#TODO update namespace to be taken as variable
def getpytorchjobstatus(interval):
    config.load_kube_config('kubeconfig')
    v1 = client.CoreV1Api()
    field_selector='reason=PyTorchJobSucceeded'
    t_sent = time.time()
    #time.sleep(2)
    #while True:
        #stream = watch.Watch().stream(v1.list_namespaced_event, "fms-tuning", field_selector=field_selector)
    for event in watch.Watch().stream(v1.list_namespaced_event, "fms-tuning", field_selector=field_selector,watch=True):
        #for event in stream:
        print(event['object'].message)
        t_now = time.time()
        if(t_now-t_sent>0):
                print("send to workload mgr")
                print(event['object'].message)
                t_sent = t_now
                #jobname = event['object'].involved_object.name
                #pod_list = v1.list_namespaced_pod(namespace='fms-tuning', label_selector='training.kubeflow.org/job-name={}'.format(jobname))
                #podname = {jobname:[]}
                #for item in pod_list.items:
                #      podname[jobname].append(item.spec.node_name)
                #      #print(item.spec.node_name)
                #      print(podname)
                
        #time.sleep(interval)
		
             
tp = 10
getpytorchjobstatus(tp)

