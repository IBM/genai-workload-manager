# Workload manager

To run, first login to the oc cluster.

Run the monitoring component first:
```
MHOST='0.0.0.0' MPORT=6000 python3 monitor.py
```

Then, run the manager by passing an input yaml:
```
python3 manager.py <file>.yaml
```

Currently, the manager supports pod, job and PyTorch job. An example file for each is also in the repo.
