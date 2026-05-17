.PHONY: help install serve demo eval eval-fidelity corpus corpus-dry product-index finetune paper test lint format clean

help:
	@echo "Naija Persona Agent — make targets"
	@echo ""
	@echo "  install         pip install -r requirements.txt"
	@echo "  serve           Run FastAPI on http://localhost:8765 (no Docker)"
	@echo "  demo            Run the Streamlit judge demo on http://localhost:8501"
	@echo ""
	@echo "  eval            Full GT eval (RMSE / BERTScore / ROUGE / AgentSociety)"
	@echo "  eval-fidelity   No-GT register-fidelity eval (no test set needed)"
	@echo ""
	@echo "  corpus          Build the full NaijaReviewer-8B fine-tune corpus (~3hrs, 1-15 USD)"
	@echo "  corpus-dry      Probe-build (50 rows per source, ~30s)"
	@echo "  corpus-stage-N  Re-run a single stage (1..6)"
	@echo "  product-index   Build the Chroma product index from the Jumia catalogue"
	@echo "  finetune        Kick off NaijaReviewer-8B QLoRA training"
	@echo ""
	@echo "  paper           Compile paper.tex → paper.pdf"
	@echo "  test            Run pytest"
	@echo "  lint            Run ruff + mypy"
	@echo "  format          Run black + ruff format"
	@echo "  clean           Remove caches"

install:
	pip install -r requirements.txt

serve:
	uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8765

demo:
	NPA_API_URL=http://localhost:8765 streamlit run demo/streamlit_app.py

eval:
	python scripts/eval_all.py --n 40 --n-scenarios 15

eval-fidelity:
	python scripts/eval_register_fidelity.py --concurrency 3

corpus:
	python scripts/build_finetune_corpus.py

corpus-dry:
	python scripts/build_finetune_corpus.py --dry-run -v

corpus-stage-1:
	python scripts/build_finetune_corpus.py --stage 1 -v
corpus-stage-2:
	python scripts/build_finetune_corpus.py --stage 2 -v
corpus-stage-3:
	python scripts/build_finetune_corpus.py --stage 3 -v
corpus-stage-4:
	python scripts/build_finetune_corpus.py --stage 4 -v
corpus-stage-5:
	python scripts/build_finetune_corpus.py --stage 5 -v
corpus-stage-6:
	python scripts/build_finetune_corpus.py --stage 6 -v

product-index:
	python scripts/build_product_index.py

finetune:
	python finetuning/train_naija_reviewer.py --config finetuning/configs/naija_reviewer_qlora.yaml

paper:
	cd paper && pdflatex paper.tex && bibtex paper && pdflatex paper.tex && pdflatex paper.tex

test:
	pytest tests/ -v

lint:
	ruff check app/ tests/
	mypy app/ || true

format:
	black app/ tests/ finetuning/
	ruff format app/ tests/ finetuning/

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
