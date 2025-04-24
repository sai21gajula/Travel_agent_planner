import json, time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from .metrics import load_refs, rouge, bleu, ragus
from .templates import MARKDOWN_HEADER

def evaluate_now(summary_path: str | Path,
                 ref_dir: str | Path,
                 meta: Dict[str, Any] | None = None) -> Path:
    summary_path = Path(summary_path)
    ref_dir = Path(ref_dir)
    refs = load_refs(ref_dir)
    concat_refs = "\n".join(refs)

    # Run metrics
    r_scores = rouge(summary_path.read_text(), concat_refs)
    b_scores, b_avg = bleu(summary_path.read_text(), refs)
    ragu = ragus(summary_path.read_text(), refs)

    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary_file": str(summary_path),
        "references_dir": str(ref_dir),
        "auto": {
            "rouge": r_scores,
            "bleu": {"per_reference": b_scores, "average": b_avg},
            "ragus": ragu
        },
        "meta": meta or {}
    }

    # Save JSON
    out_json = summary_path.with_name(summary_path.stem + "_eval.json")
    out_json.write_text(json.dumps(payload, indent=2))

    # Save Markdown report
    md = MARKDOWN_HEADER.format(
        r1=r_scores['rouge1']['f1'],
        r2=r_scores['rouge2']['f1'],
        rl=r_scores['rougeL']['f1'],
        bleu=b_avg,
        ragus=ragu
    )
    out_md = summary_path.with_name(summary_path.stem + "_eval.md")
    out_md.write_text(md)

    return out_json
