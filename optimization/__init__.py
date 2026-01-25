"""
Optimization Package for Token Reduction

Provides tools for reducing token usage while preserving information:
- Summarizer: Large response summarization using Haiku
- TOONFormatter: Token-Optimized Object Notation (30-60% savings)
- ContextCompressor: Governance context compression

Token Savings Summary:
- Summarization: 60-80% reduction on large responses
- TOON format: 30-60% reduction on structured data
- Context compression: 50-70% reduction on governance context

Usage:
    from optimization import Summarizer, TOONFormatter, ContextCompressor

    # Summarize large response
    summarizer = Summarizer()
    summary = await summarizer.summarize(large_text, intent="find auth bugs")

    # Compress structured data
    formatter = TOONFormatter()
    toon_str = formatter.to_toon({"name": "John", "age": 30})  # "name:John|age:30"

    # Compress governance context
    compressor = ContextCompressor()
    compressed = compressor.compress(governance_text, target_tokens=2000)
"""

from .summarizer import Summarizer, summarize_text
from .toon_format import TOONFormatter, to_toon, from_toon
from .context_compressor import ContextCompressor, compress_context

__all__ = [
    "Summarizer",
    "summarize_text",
    "TOONFormatter",
    "to_toon",
    "from_toon",
    "ContextCompressor",
    "compress_context",
]
