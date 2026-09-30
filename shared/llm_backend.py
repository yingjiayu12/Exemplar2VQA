"""Unified text-generation backend for vLLM and Hugging Face Transformers."""

import gc
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class GenerationConfig:
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 2048


class TextGenerationBackend:
    """Generate chat completions with vLLM or Transformers."""

    def __init__(self, model_path: str, max_model_len: int = 8192):
        self.model_path = model_path
        self.max_model_len = int(
            os.environ.get("EXEMPLAR2VQA_MAX_INPUT_TOKENS", str(max_model_len))
        )
        self.backend = os.environ.get("EXEMPLAR2VQA_LLM_BACKEND", "auto").lower()
        self.model = None
        self.tokenizer = None
        self._vllm_sampling_params = None
        self._load()

    def _load(self):
        if self.backend not in {"auto", "vllm", "transformers", "openai"}:
            raise ValueError(
                "EXEMPLAR2VQA_LLM_BACKEND must be auto, vllm, transformers, or openai."
            )

        if self.backend == "openai":
            self._load_openai()
            return

        if self.backend in {"auto", "vllm"}:
            try:
                self._load_vllm()
                return
            except (ImportError, ModuleNotFoundError) as exc:
                if self.backend == "vllm":
                    raise
                print(f"[Info] vLLM is unavailable ({exc}); using Transformers.")

        self._load_transformers()

    def _load_vllm(self):
        from vllm import LLM, SamplingParams

        print(f"=== Loading {self.model_path} with vLLM ===")
        kwargs = {
            "model": self.model_path,
            "trust_remote_code": True,
            "tensor_parallel_size": int(
                os.environ.get("EXEMPLAR2VQA_TENSOR_PARALLEL_SIZE", "1")
            ),
            "gpu_memory_utilization": float(
                os.environ.get("EXEMPLAR2VQA_GPU_MEMORY_UTILIZATION", "0.9")
            ),
            "max_model_len": self.max_model_len,
            "enforce_eager": True,
        }
        if kwargs["tensor_parallel_size"] > 1:
            kwargs["distributed_executor_backend"] = "ray"
        self.model = LLM(**kwargs)
        self.tokenizer = self.model.get_tokenizer()
        self._vllm_sampling_params = SamplingParams
        self.backend = "vllm"

    def _load_transformers(self):
        import torch
        from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

        print(f"=== Loading {self.model_path} with Transformers ===")
        config = AutoConfig.from_pretrained(self.model_path, trust_remote_code=True)
        model_type = getattr(config, "model_type", "")
        load_kwargs = {
            "trust_remote_code": True,
            "torch_dtype": "auto",
            "low_cpu_mem_usage": True,
        }

        if torch.cuda.is_available():
            load_kwargs.update(
                {
                    "device_map": "auto",
                    "max_memory": {
                        0: os.environ.get(
                            "EXEMPLAR2VQA_TRANSFORMERS_GPU_MEMORY", "4GiB"
                        ),
                        "cpu": os.environ.get(
                            "EXEMPLAR2VQA_TRANSFORMERS_CPU_MEMORY", "24GiB"
                        ),
                    },
                    "attn_implementation": os.environ.get(
                        "EXEMPLAR2VQA_ATTENTION_IMPLEMENTATION", "sdpa"
                    ),
                }
            )

        if model_type == "qwen2_5_vl":
            from transformers import Qwen2_5_VLForConditionalGeneration

            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                self.model_path, **load_kwargs
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path, **load_kwargs
            )

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, trust_remote_code=True
        )
        self.model.eval()
        self.backend = "transformers"

    def _load_openai(self):
        self.api_key = os.environ.get("EXEMPLAR2VQA_API_KEY") or os.environ.get(
            "OPENAI_API_KEY"
        )
        if not self.api_key:
            raise ValueError(
                "Set EXEMPLAR2VQA_API_KEY or OPENAI_API_KEY for the OpenAI backend."
            )
        self.api_base = os.environ.get(
            "EXEMPLAR2VQA_API_BASE", "https://qmapi.woa.com/v1"
        ).rstrip("/")
        self.api_model = os.environ.get("EXEMPLAR2VQA_API_MODEL", self.model_path)
        self.api_timeout = int(os.environ.get("EXEMPLAR2VQA_API_TIMEOUT", "600"))
        self.api_retries = int(os.environ.get("EXEMPLAR2VQA_API_RETRIES", "3"))
        self.backend = "openai"
        print(f"=== Using OpenAI-compatible API model: {self.api_model} ===")

    def format_chat(self, messages):
        if self.backend == "openai":
            return messages
        return self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

    def generate_prompts(self, prompts, config: GenerationConfig):
        max_tokens_override = os.environ.get("EXEMPLAR2VQA_MAX_NEW_TOKENS")
        if max_tokens_override:
            config = GenerationConfig(
                temperature=config.temperature,
                top_p=config.top_p,
                max_tokens=min(config.max_tokens, int(max_tokens_override)),
            )

        if self.backend == "openai":
            return [self._generate_openai(messages, config) for messages in prompts]

        if self.backend == "vllm":
            sampling = self._vllm_sampling_params(
                temperature=config.temperature,
                top_p=config.top_p,
                max_tokens=config.max_tokens,
            )
            outputs = self.model.generate(prompts, sampling)
            return [output.outputs[0].text for output in outputs]

        return [self._generate_transformers(prompt, config) for prompt in prompts]

    def generate_messages(self, messages, config: GenerationConfig) -> str:
        if self.backend == "openai":
            return self._generate_openai(messages, config)
        return self.generate_prompts([self.format_chat(messages)], config)[0]

    def _generate_openai(self, messages, config: GenerationConfig) -> str:
        payload = {
            "model": self.api_model,
            "messages": messages,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "max_tokens": config.max_tokens,
        }
        request = urllib.request.Request(
            f"{self.api_base}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        for attempt in range(1, self.api_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.api_timeout) as response:
                    result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as exc:
                error_body = exc.read().decode("utf-8", errors="replace")
                if attempt >= self.api_retries or exc.code not in {429, 500, 502, 503, 504}:
                    raise RuntimeError(
                        f"OpenAI-compatible API returned HTTP {exc.code}: {error_body}"
                    ) from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt >= self.api_retries:
                    raise RuntimeError(f"OpenAI-compatible API request failed: {exc}") from exc
            time.sleep(min(2 ** attempt, 10))
        raise RuntimeError("OpenAI-compatible API request failed after retries.")

    def _generate_transformers(self, prompt: str, config: GenerationConfig) -> str:
        import torch

        self.tokenizer.truncation_side = "left"
        tokenized = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_model_len,
        )
        input_device = self.model.get_input_embeddings().weight.device
        tokenized = {key: value.to(input_device) for key, value in tokenized.items()}
        generation_kwargs = {
            "max_new_tokens": config.max_tokens,
            "do_sample": config.temperature > 0,
            "pad_token_id": self.tokenizer.eos_token_id,
        }
        if config.temperature > 0:
            generation_kwargs.update(
                {"temperature": config.temperature, "top_p": config.top_p}
            )

        with torch.inference_mode():
            output_ids = self.model.generate(**tokenized, **generation_kwargs)
        generated_ids = output_ids[0, tokenized["input_ids"].shape[1] :]
        return self.tokenizer.decode(generated_ids, skip_special_tokens=True)

    def close(self):
        self.model = None
        self.tokenizer = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
