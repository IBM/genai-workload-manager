#!/bin/bash

output_dir='/cos1/output/sg/fine-tuned-tiny-llama-new'

# Get the integer value from the command-line argument
if [ $# -ne 1 ]; then
    echo "Usage: $0 <num_jobs_to_clean>"
    exit 1
fi

# Convert the string to an integer
n_jobs=$((10#$1))

for i in $(seq 1 $n_jobs); do
    dir=$(echo $output_dir$i)
    rm -rf $dir/checkpoint-*
    rm -rf $dir/training_logs.jsonl
    echo "Cleaning up " $dir
    ./main.py delete -n genai-job$i
done

pkill fastapi
pkill -9 -f pytorchstatus.py

