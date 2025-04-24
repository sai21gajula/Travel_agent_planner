from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Tuple
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
from rapidfuzz.fuzz import ratio
try:
    from rapidfuzz.string_metric import jaro_winkler_similarity
except ImportError:
    from rapidfuzz.distance import JaroWinkler
    jaro_winkler_similarity = JaroWinkler.similarity

nltk.download('punkt', quiet=True)

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8").strip()

def load_refs(ref_dir: Path) -> List[str]:
    return [_read(p) for p in sorted(ref_dir.glob("*.txt"))]

# ---------- ROUGE ----------
def rouge(summary: str, refs_concat: str) -> Dict:
    scorer = rouge_scorer.RougeScorer(['rouge1','rouge2','rougeL'], use_stemmer=True)
    scores = scorer.score(refs_concat, summary)
    return {k: dict(precision=v.precision, recall=v.recall, f1=v.fmeasure) for k, v in scores.items()}

# ---------- BLEU ----------
def bleu(summary: str, refs: List[str]) -> Tuple[List[float], float]:
    smooth = SmoothingFunction().method3
    scores = [
        sentence_bleu(
            [nltk.word_tokenize(r.lower())],
            nltk.word_tokenize(summary.lower()),
            weights=(0.25,0.25,0.25,0.25),
            smoothing_function=smooth
        ) for r in refs
    ]
    return scores, (sum(scores)/len(scores) if scores else 0.0)

# ---------- tiny, fast RAG-US proxy ----------
def ragus(summary: str, refs: List[str]) -> float:
    """Very light-weight faithfulness proxy:
       average max-similarity sentence-to-evidence (0-1)."""
    from nltk.tokenize import sent_tokenize
    ref_blob = "\n".join(refs)
    sent_scores = [
        max(jaro_winkler_similarity(s.lower(), r.lower()) for r in refs)
        for s in sent_tokenize(summary)
    ]
    return sum(sent_scores) / len(sent_scores) if sent_scores else 0.0
