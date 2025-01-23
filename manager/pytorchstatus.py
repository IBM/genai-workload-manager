from kubernetes import client, config,watch
from datetime import date, datetime, time, timedelta, timezone
import time
import sys
import requests
import json
from manager import scale

def load_config():
    try:
        config.load_kube_config('kubeconfig')
    except Exception as e:
        config.load_incluster_config()

def update_job(jobname):
        jobstatus = {"job_name": jobname, "status": "completed"}
        headers = {"Content-Type": "application/json"}
        def_url = "http://job-metadata-manager-service.fms-tuning.svc.cluster.local:5000/update_job_status"
        url = sys.argv[2] if len(sys.argv) >= 2 else def_url
        resp = requests.put(url, json=jobstatus, headers=headers)
        if resp.status_code != 200:
            print("Updating job status failed: ", resp.json())
        else:
            print("Updated job status")

def getpytorchjobstatus(interval=10):
    load_config()
    v1 = client.CoreV1Api()
    field_selector='reason=PyTorchJobSucceeded'

    time_diff=int(sys.argv[1]) if len(sys.argv) > 1 else interval
    t_sent = datetime.now() - timedelta(minutes = time_diff)

    for event in watch.Watch().stream(v1.list_namespaced_event, "fms-tuning", field_selector=field_selector,watch=True):
        t_event = event['object'].metadata.creation_timestamp
        t_now = datetime.now(timezone.utc)
        curr_diff = t_now - t_event
        print(f"{event['object'].message} with time diff {curr_diff}")
        if(curr_diff < timedelta(minutes=time_diff)):
                jobname = event['object'].involved_object.name
                update_job(jobname)
                #print("Calling scale")
                #scale()
        else:
            print("Event too old, not calling manager")

#donot send event notification older than `tp` minutes             
tp = 10
getpytorchjobstatus(tp)
