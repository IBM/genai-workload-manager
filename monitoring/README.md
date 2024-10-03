# Monitoring Component of GenAI workload Manager

The component currently exposes two apis:
- `/resourcequota/<namespace>`: To get gpu resource quota limit and usage for a namespace in the cluster. Assumes the kubeconfig file exists. Add the kubeconfig file in this folder for correct access.
- `freegpu`: Provides a list of nodes and their free gpus. TODO: add headers from config file. Add the correct auth key in header (L25)
