from flask import Flask, request, jsonify
from datetime import datetime
import os
import json
import logging
from collections import deque
import pickle
import requests


app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

COMPLETED_STATUS = "completed"
#threshold value is in seconds
NEXT_CHECKPOINT_THRESHOLD = int(os.environ.get("NEXT_CHECKPOINT_THRESHOLD", "60"))
#TODO: put default after checking with Kavya
MANAGER_API_URL = os.environ.get("MANAGER_API_URL")

DATA_FILE = '/data/seep/jobs_metadata.json'
#DATA_FILE = './jobs_metadata.json'
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)  # Initialize with an empty dictionary

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        jobs = json.load(f)
else:
    jobs = {}

def save_jobs_to_storage():
    with open(DATA_FILE, "w") as f:
        json.dump(jobs, f, indent=4)

job_scale_up_q = deque()
JOBS_TO_SCALE_UP_FILE = '/data/seep/jobs_to_scale_up'
#JOBS_TO_SCALE_UP_FILE = './jobs_to_scale_up'
def save_jobs_to_scale_up_to_storage():
    with open(JOBS_TO_SCALE_UP_FILE, "wb") as f:
        pickle.dump(list(job_scale_up_q), f)

if os.path.exists(JOBS_TO_SCALE_UP_FILE) and os.path.getsize(JOBS_TO_SCALE_UP_FILE) > 0:
    with open(JOBS_TO_SCALE_UP_FILE, "rb") as f:
        job_scale_up_q = pickle.load(f)

@app.route('/add_job', methods=['POST'])
def add_job():
    data = request.json
    job_name = data.get('job_name')

    if not job_name:
        return jsonify({"error": "job_name is required"}), 400

    if job_name in jobs:
        return jsonify({"error": "Job with this job_name already exists"}), 400

    mandatory_fields = ["gpu_req", "gpu_lim", "gpu_assigned"]
    for field in mandatory_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    # Default job_arrival_time to current epoch time if not provided
    job_arrival_time = data.get("job_arrival_time", int(datetime.utcnow().timestamp()))

    job = {
        "job_name": job_name,
        "gpu_req": data["gpu_req"],
        "gpu_lim": data["gpu_lim"],
        "gpu_assigned": data["gpu_assigned"],
        "replicas": data.get("replicas", 1),
        "total_epochs": data.get("total_epochs", 0),
        "job_arrival_time": job_arrival_time,
        "last_checkpoint_time": job_arrival_time,  # Initialize to job_arrival_time
        "completed_epochs": 0,
        "time_bw_checkpoints": None,
        "status": "scheduled"
    }
    jobs[job_name] = job
    save_jobs_to_storage()

    logging.info(f"Added new job: {job_name}")
    return jsonify({"message": "Job added successfully", "job": job}), 201

@app.route('/update_last_checkpoint', methods=['PUT'])
def update_last_checkpoint():
    data = request.json
    job_name = data.get('job_name')
    last_checkpoint_time = data.get('last_checkpoint_time')
    completed_epochs = data.get('completed_epochs')
    total_epochs = data.get('total_epochs')

    if not job_name or last_checkpoint_time is None or completed_epochs is None or total_epochs is None:
        return jsonify({"error": "job_name, last_checkpoint_time, completed_epochs and total_epochs are required"}), 400

    job = jobs.get(job_name)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    prev_time = job["last_checkpoint_time"]
    time_diff = last_checkpoint_time - prev_time

    job["last_checkpoint_time"] = last_checkpoint_time
    job["completed_epochs"] = completed_epochs
    job["time_bw_checkpoints"] = time_diff
    job["total_epochs"] = total_epochs

    save_jobs_to_storage()

    logging.info(f"Updated checkpoint for job: {job_name}")

    # 1: If this job is waiting to be scaled up, call the manager API
    if len(job_scale_up_q) > 0 and job_scale_up_q[0] == job_name:
        # Send a request to the manager API to scale up the job
        try:
            response = requests.post(f"{MANAGER_API_URL}/{job_name}")
            if response.status_code in [200, 201]:
                # If the response is 200 or 201, remove the job from the scale-up queue
                job_scale_up_q.popleft()
                logging.info(f"Manager notified to scale up Job {job_name}. It is removed from the queue.")
                save_jobs_to_scale_up_to_storage()
            else:
                logging.error(f"Failed to notify manager to scale up job {job_name}. Received status code: {response.status_code}")
        except requests.RequestException as e:
            logging.error(f"Error occurred while sending notification to manager to scale up job {job_name}: {e}")

    return jsonify({"message": "Job updated successfully", "job": job}), 200

def find_job_to_scale_up():
    # 1. Select only jobs where assigned is less than limit, the job status is not completed and it is already added to jobs to scaled up queue
    eligible_jobs = [job for job in jobs.values() if job["gpu_assigned"] < job["gpu_lim"] and job["status"] != COMPLETED_STATUS and job["job_name"] not in job_scale_up_q]

    # 2. Select only jobs where next checkpoint is within a threshold
    #now = int(datetime.utcnow().timestamp())
    #checkpoint_filtered_jobs = [job for job in eligible_jobs if job["completed_epochs"] == 0 or now <= (job["last_checkpoint_time"] + job["time_bw_checkpoints"]) <= now + NEXT_CHECKPOINT_THRESHOLD] 

    # 3. Sort the jobs by percentage of epochs completed i.e completed_epochs / total_epochs, with total_epochs=0 at the end
    sorted_jobs = sorted(
        eligible_jobs,
        #checkpoint_filtered_jobs,
        key=lambda job: job["completed_epochs"] / job["total_epochs"]
        if job["total_epochs"] > 0 else float('-inf'),
        reverse=True
    )

    # 4. Return the job at the top of the list
    selected_job = sorted_jobs[0]["job_name"] if sorted_jobs else None
    if selected_job == None:
        logging.error("No job available to be scaled up")
    logging.info(f"Job {selected_job}: selected for scale up")
    return selected_job
   
@app.route('/update_job_status', methods=['PUT'])
def update_job_status():
    data = request.json
    job_name = data.get('job_name')
    status = data.get('status')

    if not job_name or not status:
        return jsonify({"error": "job_name and status are required"}), 400

    job = jobs.get(job_name)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    job["status"] = status

    save_jobs_to_storage()

    logging.info(f"Updated status for job: {job_name} as {status}")

    # We might have an opportunity to scale up, let us find a candidate job for scale up
    if status == COMPLETED_STATUS:
        # 0. Remove this job from the scale up queue
        if job_name in job_scale_up_q:
            job_scale_up_q.remove(job_name)
            save_jobs_to_scale_up_to_storage()

        # 1. Find a job to scale up
        job_to_scale_up = find_job_to_scale_up()
        # 2. Add the job to the queue of jobs to be scaled up
        if job_to_scale_up != None:
            job_scale_up_q.append(job_to_scale_up)
            logging.info(f"Job {job_to_scale_up}: added to the queue of jobs to scale up")
            
            # 3. Save the queue to storage to handle failures
            save_jobs_to_scale_up_to_storage()

    return jsonify({"message": "Job updated successfully", "job": job}), 200


@app.route('/update_job', methods=['PUT'])
def update_job():
    data = request.json
    job_name = data.get('job_name')

    if not job_name:
        return jsonify({"error": "job_name is required"}), 400

    job = jobs.get(job_name)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    job.update(data)

    save_jobs_to_storage()

    logging.info(f"Updated job: {job_name}")
    return jsonify({"message": "Job updated successfully", "job": job}), 200


@app.route('/delete_job', methods=['DELETE'])
def delete_job():
    data = request.json
    job_name = data.get('job_name')

    if not job_name:
        return jsonify({"error": "job_name is required"}), 400

    job = jobs.pop(job_name, None)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    save_jobs_to_storage()

    if job_name in job_scale_up_q:
        job_scale_up_q.remove(job_name)
        save_jobs_to_scale_up_to_storage()

    logging.info(f"Deleted job: {job_name}")
    return jsonify({"message": "Job deleted successfully"}), 200

@app.route('/get_job/<job_name>', methods=['GET'])
def get_job(job_name):
    job = jobs.get(job_name)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job), 200

# API to get all jobs without any sorting or filtering
@app.route('/get_all_jobs', methods=['GET'])
def get_all_jobs():
    return jsonify(list(jobs.values())), 200

# API to get all jobs sorted by job_arrival_time (increasing)
@app.route('/get_jobs_by_arrival', methods=['GET'])
def get_jobs_by_arrival():
    filtered_jobs = [job for job in jobs.values() if job.get("status") != COMPLETED_STATUS]
    sorted_jobs = sorted(filtered_jobs, key=lambda x: x["job_arrival_time"])
    return jsonify(sorted_jobs), 200

# API to get all jobs sorted by last_checkpoint_time (decreasing) where assigned < limit
@app.route('/get_jobs_by_checkpoint_limit', methods=['GET'])
def get_jobs_by_checkpoint_limit():
    filtered_jobs = [job for job in jobs.values() if job["gpu_assigned"] < job["gpu_lim"] and job.get("status") != COMPLETED_STATUS]
    sorted_jobs = sorted(filtered_jobs, key=lambda x: x["last_checkpoint_time"], reverse=True)
    return jsonify(sorted_jobs), 200

# API to get all jobs sorted by last_checkpoint_time (decreasing) where limit - assigned == x
@app.route('/get_jobs_by_difference/<int:x>', methods=['GET'])
def get_jobs_by_difference(x):
    filtered_jobs = [job for job in jobs.values() if job["gpu_lim"] - job["gpu_assigned"] == x and job.get("status") != COMPLETED_STATUS]
    sorted_jobs = sorted(filtered_jobs, key=lambda x: x["last_checkpoint_time"], reverse=True)
    return jsonify(sorted_jobs), 200

# API to get all candidate jobs for scale down where assigned - request >= x and sorted by last_checkpoint_time (decreasing)
@app.route('/get_scale_down_jobs_by_checkpoint/<int:x>', methods=['GET'])
def get_scale_down_jobs_by_checkpoint(x):
    filtered_jobs = [job for job in jobs.values() if job["gpu_assigned"] - job["gpu_req"] >= x and job.get("status") != COMPLETED_STATUS]
    sorted_jobs = sorted(filtered_jobs, key=lambda x: x["last_checkpoint_time"], reverse=True)
    return jsonify(sorted_jobs), 200


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(host='0.0.0.0', port=port)
