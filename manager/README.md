# Workload manager

Needs login to the oc cluster to work.

## Deploy

Deploy the genai-workload-manager using the `../deployment/manager.yaml`. This launches a pod, service and RBAC.

```
oc apply -f ../deployment/manager.yaml
```

Inside the pod, go to `genai-workload-manager/manager`. The pod automatically launches the monitoring component in the background.

### Running

To deploy a pytorchjob:

```
python manager.py deploy -f <job>.yaml
```

### Scaling

`pytorchstatus.py` needs to be running to catch the completion events and notify the job manager of the same.

When a job completes, a job is chosen for scaling and is scaled automatically (default) or scaled after its checkpointing is complete (mvp2 branch).

The `orchestrator.sh` script can be used to launch the helper scripts and  multiple jobs.

### Deleting
The cleanup actions needed when deleting a launched job are invoking the delete API of the manager `python manager.py delete -n <job_name>` which will remove the job metadata from the metadata manager.

For demo purpose: We also need to remove the checkpoint folder if the same job will be launched again.

## Run locally
(This no longer works locally after support for job-metadata-manager which also needs to run as a service)

Run the monitoring component first:
```
MHOST='0.0.0.0' MPORT=6000 python3 monitor.py
```

Then, run the manager and pass input yaml:
```
python3 manager.py deploy -f sample-pytorchjob.yaml
```

Currently, the manager supports pod, job and PyTorch job. An example file for each is also in the `yamls/` directory.

To run the scaling manually, run:
```
python3 manager.py scale --name sample-pytorchjob
```

Currently, you can see the scale functionality quickly in action using the `scale.yaml`, which is a hand-crafted yaml where the pods are allocated 1 GPU each, while the annotations show that they can go up to 3 GPUs.

Deploy the job first and then run scale:
```
oc deploy -f scale.yaml
python3 manager.py scale --name sample-pytorchjob
```

If atleast 2/3 GPUs are available, then the script will patch the pytorch yaml and kill the pod to ensure new pod comes up.

## Debugging 
### Job manager 

To see if job has reached job manager

```
curl http://job-metadata-manager-service.fms-tuning.svc.cluster.local:5000/get_jobs_by_checkpoint_limit
```

### Deleting jobs
```
./main.py delete -n genai-job1 -n genai-job2 -n genai-job3 -n genai-job4
```

curl http://job-metadata-manager-service.fms-tuning.svc.cluster.local:5000/get_all_jobs


### API server for scaling
Run as 
```
fastapi run main.py
```
