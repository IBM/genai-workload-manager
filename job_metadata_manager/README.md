
# Job Metadata Manager

This is a Flask-based Python application for managing job metadata. It provides APIs to add, update, retrieve, and delete job data. Metadata is stored persistently in a file that can be mounted on a volume in a containerized environment.

## Features
- **Add a job** with required metadata.
- **Update last checkpoint** for a job, including computing time between checkpoints.
- **Delete a job** by its `job_id`.
- **Retrieve jobs** based on various filters and sorting criteria.
- Persistent storage using a mounted file (`jobs_metadata.json`).

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone git@github.ibm.com:ai-platform-engg-irl/genai-workload-manager.git
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

---

## API Endpoints

### Add Job
**Endpoint:** `/add_job`  
**Method:** `POST`

**Sample Request:**
```bash
curl -X POST http://127.0.0.1:5000/add_job -H "Content-Type: application/json" -d '{
  "job_id": "job_1",
  "gpu_req": 2,
  "gpu_lim": 4,
  "gpu_assigned": 2,
  "replicas": 1,
  "total_epochs": 100
}'
```

---

### Update Last Checkpoint
**Endpoint:** `/update_last_checkpoint`  
**Method:** `PUT`

**Sample Request:**
```bash
curl -X PUT http://127.0.0.1:5000/update_last_checkpoint -H "Content-Type: application/json" -d '{
  "job_id": "job_1",
  "last_checkpoint_time": 1701234567,
  "completed_epochs": 10
}'
```

---

### Delete Job
**Endpoint:** `/delete_job`  
**Method:** `DELETE`

**Sample Request:**
```bash
curl -X DELETE http://127.0.0.1:5000/delete_job -H "Content-Type: application/json" -d '{"job_id": "job_1"}'
```

---

### Get Job by ID
**Endpoint:** `/get_job/<job_id>`  
**Method:** `GET`

**Sample Request:**
```bash
curl http://127.0.0.1:5000/get_job/job_1
```

---

### Get All Jobs (Sorted by Arrival Time)
**Endpoint:** `/get_jobs_by_arrival`  
**Method:** `GET`

**Sample Request:**
```bash
curl http://127.0.0.1:5000/get_jobs_by_arrival
```

---

### Get Jobs (Sorted by Checkpoint Time, Limit-Assigned > 0)
**Endpoint:** `/get_jobs_by_checkpoint_limit`  
**Method:** `GET`

**Sample Request:**
```bash
curl http://127.0.0.1:5000/get_jobs_by_checkpoint_limit
```

---

### Get Jobs (Sorted by Checkpoint Time, Limit-Assigned == X)
**Endpoint:** `/get_jobs_by_difference/<x>`  
**Method:** `GET`

**Sample Request:**
```bash
curl http://127.0.0.1:5000/get_jobs_by_difference/2
```

---

