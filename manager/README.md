# Workload manager

We expect this to be run in a Kubernetes cluster.

## Deploy

Deploy the genai-workload-manager using the `../deployment/manager.yaml`. This launches a pod, service and RBAC. The pod automatically launches the monitoring component in the background.

```
oc apply -f ../deployment/manager.yaml
```

The job-metadata manager should have been started already.

### Running

Exec inside the pod and go to `genai-workload-manager/manager`. We currently support deploying pods/pytorchjobs through the CLI. We are working on a REST API based service which accepts jobs through an endpoint as well to avoid exec into the pod.

To deploy a pytorchjob:

```
python main.py deploy -f <job>.yaml
```

We currently support pod, job and pytorchjob though scaling support is only for pytorchjob. Example yamls are in the [yamls](./yamls) directory. Jobs will specify a request, limit range and the manager will assign the best possible fit after examining the cluster. Finally, it will deploy the requested resource in the cluster.

### Checkpoint notification
Our modified trainer controller will notify the job metadata manager upon every checkpoint completion with details of job name, total number of epochs,  number of epochs completed etc.

### Scaling

For scaling, the `pytorchstatus.py` script needs to be running in the background to catch completion events. The script also notifies the job metadata manager of completed events.
Upon receiving a job completion event, a job is chosen for scaling and is scaled immediately (default) or after its current epoch is completed and checkpointed (mvp2 branch).

The manager also needs to be running as a service (for mvp2 branch) which can be done as:
```
fastapi run main.py
```

This allows the job-metadata-manager to invoke the scale after receiving the completion event.

The `orchestrator.sh` script can be used to launch the helper scripts and multiple jobs. NOTE: It is used to constrain the resources for running demos and therefore manually sets the resource requirements when jobs need to be scheduled. This is necessary to see scaling in action.

### Deleting
To delete a completed/running job, we must invoke the delete API of the manager `python main.py delete -n <job_name>` to remove the resource from kubernetes and the job metadata from the metadata manager.

## Run locally
(This no longer works locally after adding the job-metadata-manager which also needs to run as a service)

Run the monitoring component first:
```
MHOST='0.0.0.0' MPORT=6000 python3 monitor.py
```

Then, run the manager and pass input yaml:
```
python3 main.py deploy -f sample-pytorchjob.yaml
```

Currently, the manager supports pod, job and PyTorch job. An example file for each is also in the `yamls/` directory.

To run the scaling manually, run:
```
python3 main.py scale --name sample-pytorchjob
```

Currently, you can see the scale functionality quickly in action using the `scale.yaml`, which is a hand-crafted yaml where the pods are allocated 1 GPU each, while the annotations show that they can go up to 3 GPUs.

Deploy the job first and then run scale:
```
oc deploy -f scale.yaml
python3 main.py scale --name sample-pytorchjob
```

If atleast 2/3 GPUs are available, then the script will patch the pytorch yaml and kill the pod to ensure new pod comes up.

## Debugging 
### Job manager 

Querying the job manager to check the running set of jobs:

```
curl http://job-metadata-manager-service.fms-tuning.svc.cluster.local:5000/get_jobs_by_checkpoint_limit
curl http://job-metadata-manager-service.fms-tuning.svc.cluster.local:5000/get_all_jobs
```

### Deleting jobs
```
./main.py delete -n genai-job1 -n genai-job2 -n genai-job3 -n genai-job4
```


### API server for scaling
Run as 
```
fastapi run main.py
```
