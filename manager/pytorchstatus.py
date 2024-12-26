from kubernetes import client, config,watch
import time
from manager import scale

def getpytorchjobstatus(interval):
    try:
        config.load_kube_config('kubeconfig')
    except Exception as e:
        config.load_incluster_config()

    v1 = client.CoreV1Api()
    field_selector='reason=PyTorchJobSucceeded'
    t_sent = time.time()
    for event in watch.Watch().stream(v1.list_namespaced_event, "fms-tuning", field_selector=field_selector,watch=True):
        print(event['object'].message)
        t_now = time.time()
        if(t_now-t_sent>0):
                print("send to workload mgr")
                print(event['object'].message)
                t_sent = t_now
                scale()
             
tp = 10
getpytorchjobstatus(tp)
