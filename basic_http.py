import json
import logging
import random
import math
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_probabilities(probs):
    if not isinstance(probs, list):
        raise ValueError("Probabilities must be provided as a list.")
    if len(probs) != 6:
        raise ValueError("Exactly six probability entries must be provided for outcomes 1-6.")
    for p in probs:
        if not isinstance(p, (int, float)):
            raise ValueError("Probabilities must contain only numeric values.")
        if p < 0:
            raise ValueError("Probabilities must not contain negative numbers.")
            
    total_prob = sum(probs)
    if not math.isclose(total_prob, 1.0, rel_tol=1e-7, abs_tol=1e-7):
        raise ValueError(f"Probabilities must sum to 1.0 (got {total_prob}).")

def generate_biased_number(probs):
    validate_probabilities(probs)
    outcomes = [1, 2, 3, 4, 5, 6]
    return random.choices(outcomes, weights=probs, k=1)[0]


class BiasedRandomAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        if self.path == '/generate':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error_response(400, "Missing request body")
                return
            
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error_response(400, "Invalid JSON payload")
                return
                
            if 'probabilities' not in data:
                self.send_error_response(400, "Missing 'probabilities' key in JSON")
                return
                
            probs = data['probabilities']
            try:
                result = generate_biased_number(probs)
                self.send_success_response(200, {"success": True, "result": result})
            except ValueError as e:
                self.send_error_response(400, str(e))
            except Exception as e:
                self.send_error_response(500, "Internal Server Error")
        else:
            self.send_error_response(404, "Not Found. Use POST /generate")
            
    def do_GET(self):
        self.send_error_response(405, "Method Not Allowed. Use POST /generate")

    def send_success_response(self, status_code, response_dict):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_dict).encode('utf-8'))

    def send_error_response(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "error": message}).encode('utf-8'))

class StoppableHTTPServer(HTTPServer):
    def run(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()

def start_server(host='localhost', port=8080):
    server = StoppableHTTPServer((host, port), BiasedRandomAPIHandler)
    logger.info(f"Starting server on {host}:{port}...")
    server.run()

if __name__ == '__main__':
    start_server()