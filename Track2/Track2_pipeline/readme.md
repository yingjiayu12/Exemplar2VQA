# Track 2: QA Generation

Track 2 converts the scene metadata and visible-view records produced by Track 1 into executable QA generators and validated QA pairs.

## Stages

1. `prepare_data.py` copies and normalizes Track 1 outputs.
2. `1_extract_schema.py` creates compact schemas for the metadata files.
3. `2_architect_plan.py` abstracts the QA exemplars in `Example.py` into task plans.
4. `3_coder_generate.py` generates and executes QA-generation programs.
5. `4_code_refiner.py` reviews, repairs, and retests generated programs.

## Model Selection

Track 2 uses `Qwen/Qwen3-Coder-30B-A3B-Instruct` by default. Run it locally with vLLM:

```bash
export EXEMPLAR2VQA_LLM_BACKEND=vllm
export EXEMPLAR2VQA_MODEL_PATH=Qwen/Qwen3-Coder-30B-A3B-Instruct
export EXEMPLAR2VQA_TENSOR_PARALLEL_SIZE=2
```

A closed-source model can be selected through any OpenAI-compatible API without changing the existing Prompts:

```bash
export EXEMPLAR2VQA_LLM_BACKEND=openai
export EXEMPLAR2VQA_API_BASE=https://api.openai.com/v1
export EXEMPLAR2VQA_API_MODEL=gpt-5.5
export EXEMPLAR2VQA_API_KEY=YOUR_API_KEY
```

Model identifiers depend on the API provider. Never commit API keys to the repository.

## Usage

Run from any directory:

```bash
bash Track2/Track2_pipeline/run.sh [TRACK1_OUTPUT] [TRACK2_DATA] [TASK_KEY]
```

All arguments are optional. By default, Track 1 outputs are read from `Track1/data/collected`, prepared data is written to `Track2/Track2_pipeline/data`, and every discovered scene is processed.

