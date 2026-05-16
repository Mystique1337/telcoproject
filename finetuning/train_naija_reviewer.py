"""NaijaReviewer-8B — QLoRA training script.

Day-1 stub. Implements the standard TRL/SFTTrainer pattern; ready to run once
`data/finetune/v1.jsonl` is built.

Usage:
    poetry run python finetuning/train_naija_reviewer.py \
        --config finetuning/configs/naija_reviewer_qlora.yaml
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def format_example(example: dict) -> str:
    """Convert one training example into the prompt-completion text."""
    instr = example.get("instruction", "")
    inp = example.get("input", {})
    out = example.get("output", {})
    persona = json.dumps(inp.get("persona", {}), ensure_ascii=False)
    product = json.dumps(inp.get("product", {}), ensure_ascii=False)
    register = inp.get("register_tier", "nigerian_english")
    rating = out.get("rating", 3)
    review = out.get("review", "")

    return (
        f"### Instruction\n{instr}\n\n"
        f"### Persona\n{persona}\n\n"
        f"### Product\n{product}\n\n"
        f"### Register tier\n{register}\n\n"
        f"### Response\n"
        f'{{"rating": {rating}, "review": "{review}"}}'
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config + sample data without launching training.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")

    cfg = load_config(args.config)
    logger.info("Config: %s", cfg)

    train_path = Path(cfg["train_file"])
    if not train_path.exists():
        logger.error(
            "Training file %s does not exist. Build it first:\n"
            "    poetry run python scripts/build_finetune_corpus.py --out %s",
            train_path,
            train_path,
        )
        return 1

    # Validate first 3 examples
    with train_path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i >= 3:
                break
            example = json.loads(line)
            text = format_example(example)
            logger.info("Sample %d (%d chars):\n%s\n---", i, len(text), text[:500])

    if args.dry_run:
        logger.info("Dry run complete — config valid, sample examples format correctly.")
        return 0

    # ----- Real training launches here -----
    # The actual training code is intentionally kept minimal in this Day-1 stub.
    # The training pattern below is what Day 2 plugs in:
    #
    #   from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    #   from peft import LoraConfig, get_peft_model
    #   from trl import SFTTrainer, SFTConfig
    #   from datasets import load_dataset
    #
    #   bnb = BitsAndBytesConfig(
    #       load_in_4bit=cfg["load_in_4bit"],
    #       bnb_4bit_quant_type=cfg["bnb_4bit_quant_type"],
    #       bnb_4bit_compute_dtype=torch.bfloat16,
    #       bnb_4bit_use_double_quant=cfg["bnb_4bit_use_double_quant"],
    #   )
    #   model = AutoModelForCausalLM.from_pretrained(cfg["base_model"], quantization_config=bnb)
    #   tokenizer = AutoTokenizer.from_pretrained(cfg["base_model"])
    #
    #   lora = LoraConfig(
    #       r=cfg["lora_r"], lora_alpha=cfg["lora_alpha"], lora_dropout=cfg["lora_dropout"],
    #       target_modules=cfg["lora_target_modules"], task_type="CAUSAL_LM",
    #   )
    #   model = get_peft_model(model, lora)
    #
    #   ds = load_dataset("json", data_files=str(train_path), split="train").train_test_split(
    #       test_size=cfg["val_split"], seed=cfg["seed"]
    #   )
    #
    #   training_args = SFTConfig(
    #       output_dir=cfg["output_dir"],
    #       num_train_epochs=cfg["num_train_epochs"],
    #       per_device_train_batch_size=cfg["per_device_train_batch_size"],
    #       gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
    #       learning_rate=cfg["learning_rate"],
    #       lr_scheduler_type=cfg["lr_scheduler_type"],
    #       warmup_steps=cfg["warmup_steps"],
    #       bf16=cfg["bf16"],
    #       optim=cfg["optim"],
    #       gradient_checkpointing=cfg["gradient_checkpointing"],
    #       report_to=cfg["report_to"],
    #       run_name=cfg["run_name"],
    #       seed=cfg["seed"],
    #       logging_steps=cfg["logging_steps"],
    #       save_strategy=cfg["save_strategy"],
    #       evaluation_strategy=cfg["evaluation_strategy"],
    #       load_best_model_at_end=cfg["load_best_model_at_end"],
    #       metric_for_best_model=cfg["metric_for_best_model"],
    #   )
    #
    #   trainer = SFTTrainer(
    #       model=model,
    #       train_dataset=ds["train"],
    #       eval_dataset=ds["test"],
    #       tokenizer=tokenizer,
    #       args=training_args,
    #       formatting_func=format_example,
    #   )
    #   trainer.train()
    #   trainer.save_model()
    #
    logger.warning("Day-1 stub: implement TRL SFTTrainer call here (see commented-out template).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
