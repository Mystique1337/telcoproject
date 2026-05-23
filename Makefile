.PHONY: help install serve eval eval-fidelity product-index test lint format clean

help:
	@echo "Naija Persona Agent - make targets"
	@echo ""
	@echo "  install         pip install -r requirements.txt"
	@echo "  serve           Run FastAPI on http://localhost:8765"
	@echo ""
	@echo "  eval            Full evaluation (RMSE / BERTScore / ROUGE / NDCG@10)"
	@echo "  eval-fidelity   No-ground-truth register-fidelity eval"
	@echo "  product-index   Build the Pinecone product index from the Jumia catalogue"
	@echo ""
	@echo "  test            Run the pytest suite"
	@echo "  lint            Run ruff + mypy"
	@echo "  format          Run black + ruff format"
	@echo "  clean           Remove caches"

install:
	pip install -r requirements.txt

serve:
	uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8765

eval:
	python scripts/eval_all.py --n 40 --n-scenarios 15

eval-fidelity:
	python scripts/eval_register_fidelity.py --concurrency 3

product-index:
	python scripts/build_pinecone_index.py

test:
	pytest tests/ -v

lint:
	ruff check app/ tests/
	mypy app/ || true

format:
	black app/ tests/
	ruff format app/ tests/

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
