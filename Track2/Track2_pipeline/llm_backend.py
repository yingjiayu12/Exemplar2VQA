"""Compatibility import for the repository-level LLM backend."""

from shared.llm_backend import GenerationConfig, TextGenerationBackend

__all__ = ["GenerationConfig", "TextGenerationBackend"]
