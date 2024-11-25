from flask import Flask, request, jsonify
from datetime import datetime
import os
import json
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

DATA_FILE = './data/jobs_metadata.json'
DATA_DIR = './data'

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)  # Initialize with an empty dictionary

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as file:
        jobs = json.load(file)
else:
    jobs = {}

def save_jobs_to_storage():
    with open(DATA_FILE, "w") as file:
        json.dump(jobs, file, indent=4)

@app.route('/add_job', methods=['POST'])
def add_job():
    data = request.json
    job_id = data.get('job_id')

    if not job_id:
        return jsonify({"error": "job_id is required"}), 400

    if job_id in jobs:
        return jsonify({"error": "Job with this job_id already exists"}), 400

    mandatory_fields = ["gpu_req", "gpu_lim", "gpu_assigned"]
    for field in mandatory_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    # Default job_arrival_time to current epoch time if not provided
    job_arrival_time = data.get("job_arrival_time", int(datetime.utcnow().timestamp()))

    job = {
        "job_id": job_id,
        "gpu_req": data["gpu_req"],
        "gpu_lim": data["gpu_lim"],
        "gpu_assigned": data["gpu_assigned"],
        "replicas": data.get("replicas", 1),
        "total_epochs": data.get("total_epochs", 0),
        "job_arrival_time": job_arrival_time,
        "last_checkpoint_time": job_arrival_time,  # Initialize to job_arrival_time
        "completed_epochs": 0,
        "time_bw_checkpoints": None
    }
    jobs[job_id] = job
    save_jobs_to_storage()

    logging.info(f"Added new job: {job_id}")
    return jsonify({"message": "Job added successfully", "job": job}), 201

@app.route('/update_last_checkpoint', methods=['PUT'])
def update_last_checkpoint():
    data = request.json
    job_id = data.get('job_id')
    last_checkpoint_time = data.get('last_checkpoint_time')
    completed_epochs = data.get('completed_epochs')

    if not job_id or last_checkpoint_time is None or completed_epochs is None:
        return jsonify({"error": "job_id, last_checkpoint_time, and completed_epochs are required"}), 400

    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    prev_time = job["last_checkpoint_time"]
    time_diff = last_checkpoint_time - prev_time

    job["last_checkpoint_time"] = last_checkpoint_time
    job["completed_epochs"] = completed_epochs
    job["time_bw_checkpoints"] = time_diff

    save_jobs_to_storage()

    logging.info(f"Updated checkpoint for job: {job_id}")
    return jsonify({"message": "Job updated successfully", "job": job}), 200

@app.route('/delete_job', methods=['DELETE'])
def delete_job():
    data = request.json
    job_id = data.get('job_id')

    if not job_id:
        return jsonify({"error": "job_id is required"}), 400

    job = jobs.pop(job_id, None)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    save_jobs_to_storage()

    logging.info(f"Deleted job: {job_id}")
    return jsonify({"message": "Job deleted successfully"}), 200

@app.route('/get_job/<job_id>', methods=['GET'])
def get_job(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job), 200

# API to get all jobs sorted by job_arrival_time (increasing)
@app.route('/get_jobs_by_arrival', methods=['GET'])
def get_jobs_by_arrival():
    sorted_jobs = sorted(jobs.values(), key=lambda x: x["job_arrival_time"])
    return jsonify(sorted_jobs), 200

# API to get all jobs sorted by last_checkpoint_time (decreasing) where assigned < limit
@app.route('/get_jobs_by_checkpoint_limit', methods=['GET'])
def get_jobs_by_checkpoint_limit():
    filtered_jobs = [job for job in jobs.values() if job["gpu_assigned"] < job["gpu_lim"]]
    sorted_jobs = sorted(filtered_jobs, key=lambda x: x["last_checkpoint_time"], reverse=True)
    return jsonify(sorted_jobs), 200

# API to get all jobs sorted by last_checkpoint_time (decreasing) where limit - assigned == x
@app.route('/get_jobs_by_difference/<int:x>', methods=['GET'])
def get_jobs_by_difference(x):
    filtered_jobs = [job for job in jobs.values() if job["gpu_lim"] - job["gpu_assigned"] == x]
    sorted_jobs = sorted(filtered_jobs, key=lambda x: x["last_checkpoint_time"], reverse=True)
    return jsonify(sorted_jobs), 200

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(host='0.0.0.0', port=port)
