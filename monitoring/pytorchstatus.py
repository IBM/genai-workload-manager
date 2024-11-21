from kubernetes import client, config,watch
import time

def getpytorchjobstatus(interval):
    config.load_kube_config('kubeconfig')
    v1 = client.CoreV1Api()
    field_selector='reason=PyTorchJobSucceeded'
    while True:
        #stream = watch.Watch().stream(v1.list_namespaced_event, "fms-tuning", field_selector=field_selector)
        stream = watch.Watch().stream(v1.list_namespaced_event, "fms-tuning", field_selector=field_selector, watch=True)
        for event in stream:
            print(event['object'].message)
        time.sleep(interval)
tp = 10
getpytorchjobstatus(tp)

