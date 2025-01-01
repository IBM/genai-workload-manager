echo "Starting 1st Job"
./main.py deploy -f yamls/demo-job1.yaml
sleep $1
echo "Starting 2nd Job"
./main.py deploy -f yamls/demo-job2.yaml
sleep $2
echo "Starting 3rd Job"
./main.py deploy -f yamls/demo-job3.yaml
