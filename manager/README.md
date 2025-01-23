# Workload manager

To run, first login to the oc cluster.

Run the monitoring component first:
```
MHOST='0.0.0.0' MPORT=6000 python3 monitor.py
```

## Deploy
Then, run the manager and pass input yaml:
```
python3 manager.py deploy -f sample-pytorchjob.yaml
```

Currently, the manager supports pod, job and PyTorch job. An example file for each is also in the repo.

## Scale
To scale, run:
```
python3 manager.py scale --name sample-pytorchjob
```

We will add functionality to choose the best job to scale up in the future.

Currently, you can see the scale functionality quickly in action using the `scale.yaml`, which is a hand-crafted yaml where the pods are allocated 1 GPU each, while the annotations show that they can go up to 3 GPUs.

Deploy the job first and then run scale:
```
oc deploy -f scale.yaml
python3 manager.py scale --name sample-pytorchjob
```

If atleast 2/3 GPUs are available, then the script will patch the pytorch yaml and kill the pod to ensure new pod comes up.



## Job manager

```
curl http://job-metadata-manager-service.fms-tuning.svc.cluster.local:5000/get_jobs_by_checkpoint_limit
```

## Deleting jobs
```
./main.py delete -n genai-job1 -n genai-job2 -n genai-job3 -n genai-job4
```

curl http://job-metadata-manager-service.fms-tuning.svc.cluster.local:5000/get_all_jobs


## API server
Run as 
```
fastapi run main.py
```
