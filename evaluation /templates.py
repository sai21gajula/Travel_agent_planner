MARKDOWN_HEADER = """\
# ✍️ RAG Evaluation Report
| Metric | Value |
|--------|-------|
| ROUGE-1 F1 | {r1:.3f} |
| ROUGE-2 F1 | {r2:.3f} |
| ROUGE-L F1 | {rl:.3f} |
| Avg BLEU-4 | {bleu:.3f} |
| RAG-US (faithfulness proxy) | {ragus:.3f} |
| BERTScore | {bertscore:.3f} |
"""
