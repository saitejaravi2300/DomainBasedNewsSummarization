#!/usr/bin/env python3
"""
Test script to verify Gemma + LoRA adapter is working
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Project root - use explicit path to avoid issues with spaces in directory names
PROJECT_ROOT = Path(r"C:\Users\varun\Downloads\NLP_DOMAIN_BASED NEWS SUMMARIZATION")

# Load env from backend/.env
env_path = PROJECT_ROOT / "backend" / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"[INFO] Loaded env from: {env_path}")
else:
    print(f"[WARN] Env file not found: {env_path}")

# Read env vars
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
GEMMA_BASE_MODEL_ID = os.environ.get("GEMMA_BASE_MODEL_ID", "google/gemma-2-2b").strip() or "google/gemma-2-2b"
GEMMA_ADAPTER_DIR = os.environ.get("GEMMA_ADAPTER_DIR", "ml-lab/artifacts/stage_500/checkpoint-63").strip()
GEMMA_MAX_NEW_TOKENS = int(os.environ.get("GEMMA_MAX_NEW_TOKENS", "160") or "160")

print(f"[DEBUG] HF_TOKEN: {'SET' if HF_TOKEN else 'NOT SET'}")
print(f"[DEBUG] GEMMA_ADAPTER_DIR: {GEMMA_ADAPTER_DIR}")

print("=" * 60)
print("GEMMA + LoRA ADAPTER TEST")
print("=" * 60)

print(f"\n[1] Configuration:")
print(f"    HF_TOKEN: {'SET' if HF_TOKEN else 'NOT SET'}")
print(f"    Base Model: {GEMMA_BASE_MODEL_ID}")
print(f"    Adapter Path (raw): {GEMMA_ADAPTER_DIR}")

# Resolve adapter path - try multiple locations
possible_paths = [
    Path(GEMMA_ADAPTER_DIR),  # As-is
    Path(__file__).parent.parent / "ml-lab" / "artifacts" / "stage_500" / "checkpoint-63",  # Relative to project root
    Path(__file__).parent.parent / "backend" / ".." / "ml-lab" / "artifacts" / "stage_500" / "checkpoint-63",
    Path("C:/Users/varun/Downloads/NLP_DOMAIN_BASED NEWS SUMMARIZATION/ml-lab/artifacts/stage_500/checkpoint-63"),
]

adapter_path = None
for p in possible_paths:
    if p.exists():
        adapter_path = p.resolve()
        print(f"    Resolved Adapter: {adapter_path}")
        break

if adapter_path is None:
    print(f"\n[ERROR] Adapter path not found!")
    for p in possible_paths:
        print(f"    Tried: {p}")
    sys.exit(1)

print(f"\n[2] Loading libraries...")
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
    print("    [OK] All libraries loaded")
except ImportError as e:
    print(f"    [ERROR] Missing library: {e}")
    sys.exit(1)

print(f"\n[3] Loading tokenizer...")
try:
    tokenizer = AutoTokenizer.from_pretrained(
        GEMMA_BASE_MODEL_ID,
        token=HF_TOKEN,
        use_fast=True,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    print("    [OK] Tokenizer loaded")
except Exception as e:
    print(f"    [ERROR] Tokenizer failed: {e}")
    sys.exit(1)

print(f"\n[4] Loading base model...")
try:
    model = AutoModelForCausalLM.from_pretrained(
        GEMMA_BASE_MODEL_ID,
        token=HF_TOKEN,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    print("    [OK] Base model loaded")
except Exception as e:
    print(f"    [ERROR] Base model failed: {e}")
    sys.exit(1)

print(f"\n[5] Loading LoRA adapter...")
try:
    model = PeftModel.from_pretrained(model, str(adapter_path), token=HF_TOKEN)
    model.to("cpu")
    model.eval()
    print("    [OK] LoRA adapter loaded successfully!")
except Exception as e:
    print(f"    [ERROR] LoRA adapter failed: {e}")
    sys.exit(1)

print(f"\n[6] Testing generation...")
test_prompt = """Summarize this news article about AI:

Title: OpenAI Releases New AI Model
Description: OpenAI has released a new AI model that demonstrates improved reasoning capabilities.

Generate a JSON summary with trend_title, tldr, and summary fields."""

try:
    inputs = tokenizer(test_prompt, return_tensors="pt", truncation=True, max_length=1024)
    
    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=GEMMA_MAX_NEW_TOKENS,
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )
    
    prompt_length = inputs["input_ids"].shape[1]
    completion = tokenizer.decode(outputs[0][prompt_length:], skip_special_tokens=True)
    
    print("\n" + "=" * 60)
    print("GENERATION OUTPUT:")
    print("=" * 60)
    print(completion[:500])
    print("=" * 60)
    print("\n[OK] Gemma + LoRA is WORKING!")
    
except Exception as e:
    print(f"    [ERROR] Generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED - Gemma + LoRA is ready!")
print("=" * 60)
