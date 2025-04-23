from pathlib import Path

BASE   = Path(__file__).parent
SCHEMA = {
    "manual_criteria": {
        "faithfulness": "Does the plan stay true to agent evidence?",
        "relevance"  : "Includes the most useful info from evidence?",
        "coherence"  : "Well organised, easy to follow?",
        "conciseness": "No needless fluff?"
    },
    "manual_scale": [1, 2, 3, 4, 5]
}
