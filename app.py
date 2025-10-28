
import sys
import json
import requests
import logging

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

BASE_URL = "https://api.unhcr.org/population/v1/"

def send_response(response):
    """Sends a JSON-RPC response to stdout."""
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

def _call_unhcr_api(endpoint, params):
    """Helper function to call the UNHCR API."""
    params["cf_type"] = "ISO"
    if "year" in params and isinstance(params["year"], str):
        params["year[]"] = params.pop("year").split(",")

    # Support "true" strings for boolean flags
    for key in ["coo_all", "coa_all"]:
        if key in params and isinstance(params[key], str):
            params[key] = params[key].lower() in ["true", "1"]

    response = requests.get(f"{BASE_URL}{endpoint}/", params=params)
    response.raise_for_status()
    return response.json()

def get_population_data(**params):
    return _call_unhcr_api("population", params)

def get_asylum_applications(**params):
    return _call_unhcr_api("asylum-applications", params)

def get_asylum_decisions(**params):
    return _call_unhcr_api("asylum-decisions", params)


def handle_request(request):
    """Handles a single JSON-RPC request."""
    try:
        if request["method"] == "get_population_data":
            result = get_population_data(**request["params"])
        elif request["method"] == "get_asylum_applications":
            result = get_asylum_applications(**request["params"])
        elif request["method"] == "get_asylum_decisions":
            result = get_asylum_decisions(**request["params"])
        else:
            raise ValueError(f"Unknown method: {request['method']}")

        send_response({
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": result
        })
    except Exception as e:
        logging.error(f"Error handling request: {e}")
        send_response({
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {"code": -32000, "message": str(e)}
        })

def run_server():
    """Runs the MCP server, reading requests from stdin."""
    for line in sys.stdin:
        try:
            request = json.loads(line)
            handle_request(request)
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from stdin.")

if __name__ == "__main__":
    run_server()
