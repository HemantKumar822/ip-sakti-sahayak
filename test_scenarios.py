import json
import urllib.error
import urllib.request

API_URL = "http://127.0.0.1:8000/api/v1/query"

SCENARIOS = [
    {
        "name": "Section 3(p) / 3(d) Edge Case",
        "query": "Is Ashwagandha extract patentable if I discover a new use for it?"
    },
    {
        "name": "Biological Diversity Act (Foreign Investment)",
        "query": "Do I need NBA approval if my startup has foreign investment?"
    },
    {
        "name": "ASU Medicine Trademark",
        "query": "Can I register a trademark for a classical Ayurvedic drug name like Chyawanprash?"
    },
    {
        "name": "Out of Jurisdiction",
        "query": "How do I file a utility patent for an herbal formulation in the United States USPTO?"
    }
]

def test_scenario(scenario):
    req_body = json.dumps({
        "query_text": scenario["query"],
        "session_id": "test-scenario-runner"
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=req_body,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return {
                "name": scenario["name"],
                "query": scenario["query"],
                "status": result.get("status"),
                "confidence": result.get("confidence_score", 0),
                "grounding": result.get("grounding_score", 0),
                "tkdl_flag": result.get("tkdl_flag", False),
                "abs_flag": result.get("abs_flag", False),
                "latency": result.get("response_time_ms", 0)
            }
    except urllib.error.URLError as e:
        return {
            "name": scenario["name"],
            "query": scenario["query"],
            "error": str(e)
        }

def run_all():
    print("Running IP-SAKTI Scenario Test Suite...\n")
    results = []
    for s in SCENARIOS:
        print(f"Testing: {s['name']}...")
        res = test_scenario(s)
        results.append(res)
    
    print("\n| Scenario | Status | Confidence | Grounding | TKDL | ABS | Latency |")
    print("|----------|--------|------------|-----------|------|-----|---------|")
    for r in results:
        if "error" in r:
            print(f"| {r['name']} | ERROR: {r['error']} | - | - | - | - | - |")
        else:
            conf = f"{r['confidence']*100:.1f}%"
            ground = f"{r['grounding']*100:.1f}%"
            print(f"| {r['name']} | {r['status']} | {conf} | {ground} | {r['tkdl_flag']} | {r['abs_flag']} | {r['latency']}ms |")

if __name__ == "__main__":
    run_all()
