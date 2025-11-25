python3 pytorchstatus.py &
fastapi run main.py &
echo "Starting 1st Job"
cp ../monitoring/sample_json/outputj1.json ../monitoring/sample_json/output.json
./main.py deploy -f yamls/demo-job1.yaml
sleep $1
echo "============================================================"
echo "Starting 2nd Job"
cp ../monitoring/sample_json/outputj2.json ../monitoring/sample_json/output.json
./main.py deploy -f yamls/demo-job2.yaml
sleep $2
echo "============================================================"
echo "Starting 3rd Job"
cp ../monitoring/sample_json/outputj3.json ../monitoring/sample_json/output.json
./main.py deploy -f yamls/demo-job3.yaml
#for scale up
cp ../monitoring/sample_json/outputsup.json ../monitoring/sample_json/output.json
#for scale down
sleep $3
echo "============================================================"
echo "Starting 4th Job"
cp ../monitoring/sample_json/outputsdown.json ../monitoring/sample_json/output.json
{ sleep 20; cp ../monitoring/sample_json/outputsdown2.json ../monitoring/sample_json/output.json; } &
./main.py deploy -f yamls/demo-job4.yaml
