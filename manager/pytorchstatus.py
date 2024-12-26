from kubernetes import client, config,watch
from datetime import date, datetime, time, timedelta
import time
import sys
from manager import scale

def getpytorchjobstatus(interval):
    try:
        config.load_kube_config('kubeconfig')
    except Exception as e:
        config.load_incluster_config()

    v1 = client.CoreV1Api()
    field_selector='reason=PyTorchJobSucceeded'
    #default time diff 10 minutes
    time_diff=int(sys.argv[1]) if len(sys.argv) > 1 else interval
    t_sent = datetime.now() - timedelta(minutes = time_diff)
    for event in watch.Watch().stream(v1.list_namespaced_event, "fms-tuning", field_selector=field_selector,watch=True):
        print(event['object'].message)
        t_now = datetime.now()
        if(t_now-t_sent>0):
                print("send to workload mgr")
                print(event['object'].message)
                jobname = event['object'].involved_object.name
                headers = {"Content-Type": "application/json"}
                def_url = "http://job-metadata-manager-service.fms-tuning.svc.cluster.local:5000/update_job_status"
                url = sys.argv[2] if len(sys.argv) >= 2 else def_url
                response = requests.post(url, data=json.dumps(jobname), headers=headers)
                t_sent = t_now
                scale()
#donot send event notification older than `tp` minutes             
tp = 10
getpytorchjobstatus(tp)
