
# Job Metadata Manager

This is a Flask-based Python application for managing job metadata. It provides APIs to add, update, retrieve, and delete job data. Metadata is stored persistently in a file that can be mounted on a volume in a containerized environment.

---

## Local Setup Instructions

To deploy on K8s, use the [yaml](../deployment/job_metadata_manager.yaml). To run locally for testing etc. follow the below instructions.

### 1. Clone the Repository

```bash
git clone git@github.com:IBM/genai-workload-manager.git
cd job_metadata_manager
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up the Environment Variable

The application uses the environment variable `FLASK_PORT` to determine which port it should run on. You can set it as follows:

```bash
export FLASK_PORT=5000
```
If this variable is not set, the application will default to port `5000`.

### 4. Run the Application

```bash
python job_metadata_manager.py
```

The app will start and listen on `http://127.0.0.1:<FLASK_PORT>` (default: `5000`).


## API Endpoints

### Add Job
**Endpoint:** `/add_job`  
**Method:** `POST`

**Sample Request:**
```bash
curl -X POST http://127.0.0.1:5000/add_job -H "Content-Type: application/json" -d '{
  "job_name": "job_1",
  "gpu_req": 2,
  "gpu_lim": 4,
  "gpu_assigned": 2,
  "replicas": 1,
  "total_epochs": 100
}'
```


### Update Last Checkpoint
**Endpoint:** `/update_last_checkpoint`  
**Method:** `PUT`

**Sample Request:**
```bash
curl -X PUT http://127.0.0.1:5000/update_last_checkpoint -H "Content-Type: application/json" -d '{
  "job_name": "job_1",
  "last_checkpoint_time": 1701234567,
  "completed_epochs": 10
}'
```

### Update Last Checkpoint
**Endpoint:** `/update_job_status`
**Method:** `PUT`

**Sample Request:**
```bash
curl -X PUT http://127.0.0.1:5000/update_job_status -H "Content-Type: application/json" -d '{
  "job_name": "job_1",
  "status": "completed"
}'
```

### Delete Job
**Endpoint:** `/delete_job`  
**Method:** `DELETE`

**Sample Request:**
```bash
curl -X DELETE http://127.0.0.1:5000/delete_job -H "Content-Type: application/json" -d '{"job_name": "job_1"}'
```

### Get Job by Job name
**Endpoint:** `/get_job/<job_name>`  
**Method:** `GET`

**Sample Request:**
```bash
curl http://127.0.0.1:5000/get_job/job_1
```

### Get All Jobs (Unsorted and Unfiltered)
**Endpoint:** `/get_all_jobs`  
**Method:** `GET`

**Sample Request:**
```bash
curl http://127.0.0.1:5000/get_all_jobs
```

**Note:** All the GET APIs listed below return only jobs with a status other than "completed".


### Get All Jobs (Sorted by Arrival Time)
**Endpoint:** `/get_jobs_by_arrival`
**Method:** `GET`

**Sample Request:**
```bash
curl http://127.0.0.1:5000/get_jobs_by_arrival
```

### Get Jobs (Sorted by Checkpoint Time, Limit-Assigned > 0)
**Endpoint:** `/get_jobs_by_checkpoint_limit`  
**Method:** `GET`

**Sample Request:**
```bash
curl http://127.0.0.1:5000/get_jobs_by_checkpoint_limit
```

### Get Jobs (Sorted by Checkpoint Time, Limit-Assigned == x)
**Endpoint:** `/get_jobs_by_difference/<x>`  
**Method:** `GET`

**Sample Request:**
```bash
curl http://127.0.0.1:5000/get_jobs_by_difference/2
```

### Get Candidate Jobs for Scale Down (Assigned-Request >= x and Sorted by Checkpoint Time in decreasing order)
**Endpoint:** `/get_scale_down_jobs_by_checkpoint/<x>`
**Method:** `GET`

**Sample Request:**
```bash
curl http://127.0.0.1:5000/get_scale_down_jobs_by_checkpoint/2
```
