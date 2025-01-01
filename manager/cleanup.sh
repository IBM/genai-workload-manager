#!/bin/bash

output_dir='/cos1/output/sg/fine-tuned-tiny-llama-new'

val=1

# Get the integer value from the command-line argument
if [ $# -ne 1 ]; then
    val=$1
fi

# Convert the string to an integer
n_jobs=$((10#$val))

for i in $(seq 1 $n_jobs); do
    dir=$(echo $output_dir$i)
    rm -rf $dir/checkpoint-*
    rm -rf $dir/training_logs.jsonl
    echo "Cleaning up " $dir
done
