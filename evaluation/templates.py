MARKDOWN_HEADER = """
# 📊 Evaluation Summary

**ROUGE Scores**
- ROUGE-1 F1: `{r1:.3f}`
- ROUGE-2 F1: `{r2:.3f}`
- ROUGE-L F1: `{rl:.3f}`

**BLEU Score (Average)**: `{bleu:.3f}`  
**RAG-US Score (Faithfulness Proxy)**: `{ragus:.3f}`

---

This evaluation was automatically generated from the summary and agent raw outputs.
"""
