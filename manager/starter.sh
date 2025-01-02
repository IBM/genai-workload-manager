echo "Starting 1st Job"
cp ../monitoring/sample_json/outputj1.json ../monitoring/sample_json/output.json
./main.py deploy -f yamls/demo-job1.yaml
sleep $1
echo "Starting 2nd Job"
cp ../monitoring/sample_json/outputj2.json ../monitoring/sample_json/output.json
./main.py deploy -f yamls/demo-job2.yaml
sleep $2
echo "Starting 3rd Job"
cp ../monitoring/sample_json/outputj3.json ../monitoring/sample_json/output.json
./main.py deploy -f yamls/demo-job3.yaml
#for scale up
cp ../monitoring/sample_json/outputsup.json ../monitoring/sample_json/output.json
