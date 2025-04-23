from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Tuple
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
import rapidfuzz  # Import the full package

# Download required NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

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
    
    # Use the correct import based on the current rapidfuzz version
    try:
        from rapidfuzz.string_metric import jaro_winkler_similarity
    except ImportError:
        # Fallback to newer API structure if available
        try:
            from rapidfuzz.distance import jaro_winkler
            # In newer versions, it might be a function instead of a method
            jaro_winkler_similarity = lambda s1, s2: jaro_winkler(s1, s2)
        except ImportError:
            # Final fallback
            try:
                from rapidfuzz import jaro_winkler_similarity
            except ImportError:
                # Ultimate fallback using Levenshtein ratio
                def jaro_winkler_similarity(s1, s2):
                    from difflib import SequenceMatcher
                    return SequenceMatcher(None, s1, s2).ratio()
    
    sent_scores = [
        max(jaro_winkler_similarity(s.lower(), r.lower()) for r in refs)
        for s in sent_tokenize(summary)
    ]
    return sum(sent_scores) / len(sent_scores) if sent_scores else 0.0


# ---------- BERTScore ----------
def bert_score(summary: str, refs: list[str]) -> float:
    """Implementation of BERTScore using transformers.
    Returns a semantic similarity score between summary and references."""
    try:
        from transformers import AutoTokenizer, AutoModel
        import torch
        import torch.nn.functional as F
        
        # Load pre-trained model and tokenizer
        model_name = "bert-base-uncased"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        
        # Concatenate references
        refs_text = "\n".join(refs)
        
        # Tokenize inputs
        summary_inputs = tokenizer(summary, return_tensors="pt", padding=True, truncation=True, max_length=512)
        refs_inputs = tokenizer(refs_text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        
        # Get embeddings
        with torch.no_grad():
            summary_outputs = model(**summary_inputs)
            refs_outputs = model(**refs_inputs)
            
            # Get sentence embeddings (mean of token embeddings)
            summary_emb = mean_pooling(summary_outputs, summary_inputs['attention_mask'])
            refs_emb = mean_pooling(refs_outputs, refs_inputs['attention_mask'])
            
            # Normalize embeddings
            summary_emb = F.normalize(summary_emb, p=2, dim=1)
            refs_emb = F.normalize(refs_emb, p=2, dim=1)
            
            # Calculate cosine similarity
            similarity = torch.mm(summary_emb, refs_emb.transpose(0, 1)).item()
            
        return similarity
    except Exception as e:
        print(f"Warning: BERTScore calculation error: {str(e)}. Using RAG-US as fallback.")
        return ragus(summary, refs)

# Helper function for bert_score
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
