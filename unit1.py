"""

Mechanism:
This program uses Python random.choices() to implement weighted random number generation.
The probabilities are validated to ensure they are a list of exactly 6 non-negative numeric
values that sum to 1.0
"""

import unittest
import urllib.request
import urllib.error
import json
import threading
import time
from collections import Counter

# Import core elements from the basic_http.py containing our server and logic
from basic_http import validate_probabilities, generate_biased_number, BiasedRandomAPIHandler, StoppableHTTPServer

class TestGenerator(unittest.TestCase):
    def test_validation_exact_sum(self):
        try: validate_probabilities([0.1, 0.2, 0.3, 0.2, 0.1, 0.1])
        except ValueError: self.fail("validate_probabilities raised ValueError!")

    def test_validation_incorrect_sum(self):
        with self.assertRaisesRegex(ValueError, "sum to 1.0"):
            validate_probabilities([0.1, 0.2, 0.3, 0.2, 0.1, 0.5])

    def test_validation_not_numeric(self):
        with self.assertRaisesRegex(ValueError, "only numeric values"):
            validate_probabilities([0.1, 0.2, 0.3, 0.2, "0.1", 0.1])

    def test_validation_negative_numbers(self):
        with self.assertRaisesRegex(ValueError, "must not contain negative numbers"):
            validate_probabilities([0.1, 0.2, 0.3, 0.2, -0.1, 0.3])

    def test_validation_incorrect_length(self):
        with self.assertRaisesRegex(ValueError, "Exactly six probability"):
            validate_probabilities([0.1, 0.2, 0.3, 0.4])

    def test_validation_not_list(self):
        with self.assertRaisesRegex(ValueError, "must be provided as a list"):
            validate_probabilities({1: 0.5, 2: 0.5})
            
    def test_generator_bounds(self):
        self.assertIn(generate_biased_number([0.1, 0.2, 0.3, 0.2, 0.1, 0.1]), [1, 2, 3, 4, 5, 6])

    def test_generator_statistical_distribution(self):
        probs = [0.1, 0.2, 0.4, 0.15, 0.05, 0.1]
        iterations = 50000 
        tolerance = 0.015
        counts = Counter()
        for _ in range(iterations):
            counts[generate_biased_number(probs)] += 1
            
        for i, expected_prob in enumerate(probs):
            actual_prob = counts[i + 1] / iterations
            self.assertAlmostEqual(actual_prob, expected_prob, delta=tolerance,
                                   msg=f"Outcome {i+1} varied too much.")

class TestAPIIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We start a HTTP server in a background thread for testing
        cls.server = StoppableHTTPServer(('localhost', 8085), BiasedRandomAPIHandler)
        cls.server_thread = threading.Thread(target=cls.server.run)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(0.5)
        cls.base_url = "http://localhost:8085/generate"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server_thread.join()

    def send_post_request(self, payload):
        req = urllib.request.Request(self.base_url, method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps(payload).encode('utf-8')
        try:
            with urllib.request.urlopen(req, data=data) as response:
                return response.status, json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode('utf-8'))

    def test_valid_request(self):
        status, response = self.send_post_request({"probabilities": [0.1, 0.2, 0.3, 0.2, 0.1, 0.1]})
        self.assertEqual(status, 200)
        self.assertTrue(response.get("success"))
        self.assertIn(response.get("result"), [1, 2, 3, 4, 5, 6])

    def test_malformed_json(self):
        req = urllib.request.Request(self.base_url, method="POST")
        req.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(req, data=b"{broken_json") as r:
                status, rd = r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            status, rd = e.code, json.loads(e.read().decode())
        self.assertEqual(status, 400)
        self.assertEqual(rd.get("error"), "Invalid JSON payload")


if __name__ == '__main__':
    unittest.main()