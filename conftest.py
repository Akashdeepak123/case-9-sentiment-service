"""
Pytest configuration loaded automatically before any test imports.
Ensures HuggingFace tokenizer parallelism is disabled to prevent
macOS shutdown crashes.
"""
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
