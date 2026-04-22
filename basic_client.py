import urllib.request
import urllib.error
import json
import threading
import time

def call_api(base_url, payload):
    req = urllib.request.Request(base_url, method="POST")
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(payload).encode('utf-8')
    try:
        with urllib.request.urlopen(req, data=data) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))
    except Exception as e:
        return 500, {"error": str(e)}

def run_load_test():
    URL = "http://localhost:8080/generate"
    PAYLOAD = {"probabilities": [0.1, 0.2, 0.3, 0.2, 0.1, 0.1]}
    TOTAL_REQUESTS = 1000
    CONCURRENT_THREADS = 20
    
    results = {"successes": 0, "failures": 0, "times": []}
    lock = threading.Lock()

    def make_request():
        start_time = time.time()
        status, response = call_api(URL, PAYLOAD)
        if status == 200:
            with lock:
                results["successes"] += 1
        else:
            with lock:
                results["failures"] += 1
        with lock:
            results["times"].append(time.time() - start_time)

    print(f"Starting load test on {URL} with {TOTAL_REQUESTS} requests...")
    threads = []
    start_time = time.time()
    
    for _ in range(TOTAL_REQUESTS):
        t = threading.Thread(target=make_request)
        threads.append(t)
        t.start()
        if len(threads) >= CONCURRENT_THREADS:
            for th in threads:
                th.join()
            threads = []
    for th in threads:
        th.join()
        
    total_time = time.time() - start_time
    avg_time = sum(results["times"]) / len(results["times"]) if results["times"] else 0
        
    print("\n--- Load Test Results ---")
    print(f"Total Time Taken:     {total_time:.4f} seconds")
    print(f"Successful Requests:  {results['successes']}")
    print(f"Failed Requests:      {results['failures']}")
    print(f"Avg Response Time:    {avg_time:.4f} seconds/request")
    print(f"Requests per Second:  {TOTAL_REQUESTS / total_time:.2f} req/s")

if __name__ == '__main__':
    url = "http://localhost:8080/generate"
    data = {"probabilities": [0.1, 0.2, 0.3, 0.2, 0.1, 0.1]}
    
    print("Sending Single API Request...")
    status, response = call_api(url, data)
    print(f"HTTP {status} -> {response}")
    
    print("\nStarting Performance Load Test...")
    run_load_test()