from __future__ import annotations

import threading
from typing import Any

import numpy as np

from app.core import config as config_module


class _FakeEmbedModel:
    def encode(self, texts, convert_to_numpy=True, normalize_embeddings=True):
        if isinstance(texts, str):
            texts = [texts]
        vectors = []
        for text in texts:
            seed = float((sum(ord(c) for c in text) % 997) + 1)
            vec = np.array([seed, seed / 2.0, seed / 3.0, seed / 4.0], dtype=np.float32)
            if normalize_embeddings:
                norm = np.linalg.norm(vec) or 1.0
                vec = vec / norm
            vectors.append(vec)
        arr = np.vstack(vectors)
        return arr if convert_to_numpy else arr.tolist()


class ModelRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._embed_model: Any = None
        self._tokenizer: Any = None
        self._hf_pipe: Any = None

    def get_embed_model(self):
        settings = config_module.settings
        with self._lock:
            if self._embed_model is not None:
                return self._embed_model

            if settings.test_mode:
                self._embed_model = _FakeEmbedModel()
                return self._embed_model

            from sentence_transformers import SentenceTransformer

            self._embed_model = SentenceTransformer(settings.embed_model_id)
            return self._embed_model

    def get_llm(self):
        settings = config_module.settings
        with self._lock:
            if self._tokenizer is not None and self._hf_pipe is not None:
                return self._tokenizer, self._hf_pipe

            if settings.test_mode:
                self._tokenizer = None
                self._hf_pipe = None
                return self._tokenizer, self._hf_pipe

            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

            self._tokenizer = AutoTokenizer.from_pretrained(settings.llm_model_id)
            try:
                llm_model = AutoModelForCausalLM.from_pretrained(settings.llm_model_id, torch_dtype="auto")
            except Exception:
                llm_model = AutoModelForCausalLM.from_pretrained(settings.llm_model_id)

            self._hf_pipe = pipeline(
                "text-generation",
                model=llm_model,
                tokenizer=self._tokenizer,
                device=-1,
                max_new_tokens=150,
                do_sample=False,
                pad_token_id=self._tokenizer.eos_token_id,
            )
            return self._tokenizer, self._hf_pipe


models = ModelRegistry()
