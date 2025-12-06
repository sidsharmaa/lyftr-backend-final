from typing import Dict, Tuple

_HTTP_REQUESTS: Dict[Tuple[str, str], int] = {}
_WEBHOOK_RESULTS: Dict[str, int] = {}

def track_http_request(path: str, status_code: int):
    """
    Increments the http_requests_total counter.
    """
    key = (path, str(status_code))
    _HTTP_REQUESTS[key] = _HTTP_REQUESTS.get(key, 0) + 1

def track_webhook_result(result: str):
    """
    Increments the webhook_requests_total counter.
    Args: result (str): e.g., 'created', 'duplicate', 'invalid_signature'
    """
    _WEBHOOK_RESULTS[result] = _WEBHOOK_RESULTS.get(result, 0) + 1

def generate_prometheus_output() -> str:
    """
    Formats the current metrics into Prometheus text format.
    """
    lines = []
    
    lines.append("# HELP http_requests_total Total number of HTTP requests.")
    lines.append("# TYPE http_requests_total counter")
    for (path, status), count in _HTTP_REQUESTS.items():
        lines.append(f'http_requests_total{{path="{path}",status="{status}"}} {count}')
        
    lines.append("# HELP webhook_requests_total Total number of webhook processing outcomes.")
    lines.append("# TYPE webhook_requests_total counter")
    for result, count in _WEBHOOK_RESULTS.items():
        lines.append(f'webhook_requests_total{{result="{result}"}} {count}')
        
    return "\n".join(lines)