.PHONY: help install demo serve eval finetune paper test lint format clean down logs

help:
	@echo "Naija Persona Agent — make targets"
	@echo ""
	@echo "  install         Install Python dependencies (poetry install)"
	@echo "  serve           Run FastAPI locally with reload (no container)"
	@echo "  demo            Bring up app + ollama + chroma stack via docker compose"
	@echo "  down            Tear down the stack (volumes preserved)"
	@echo "  logs            Tail container logs"
	@echo "  corpus          Build the full NaijaReviewer-8B fine-tune corpus (~3hrs, 1-15 USD)"
	@echo "  corpus-dry      Probe-build the corpus (50 rows per source, ~30s)"
	@echo "  corpus-stage-N  Re-run a single stage (1=download, 2=rate, 3=afrisenti, 4=synthetic, 5=split, 6=card)"
	@echo "  product-index   Build the Chroma product index from Idowenst Jumia dataset"
	@echo "  eval            Run the full evaluation suite"
	@echo "  finetune        Kick off NaijaReviewer-8B QLoRA training"
	@echo "  paper           Compile paper.tex"
	@echo "  test            Run pytest"
	@echo "  lint            Run ruff + mypy"
	@echo "  format          Run black + ruff format"
	@echo "  clean           Remove caches"

install:
	poetry install --with dev,demo

serve:
	poetry run uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

demo:
	docker compose up -d
	@echo "Waiting for app to start..."
	@sleep 8
	@curl -fsS http://localhost:8000/health && echo "" && echo "✅ Demo up — visit http://localhost:8000/docs" || echo "❌ Demo failed; check logs with: make logs"

corpus:
	poetry run python scripts/build_finetune_corpus.py

corpus-dry:
	poetry run python scripts/build_finetune_corpus.py --dry-run -v

corpus-stage-1:
	poetry run python scripts/build_finetune_corpus.py --stage 1 -v

corpus-stage-2:
	poetry run python scripts/build_finetune_corpus.py --stage 2 -v

corpus-stage-3:
	poetry run python scripts/build_finetune_corpus.py --stage 3 -v

corpus-stage-4:
	poetry run python scripts/build_finetune_corpus.py --stage 4 -v

corpus-stage-5:
	poetry run python scripts/build_finetune_corpus.py --stage 5 -v

corpus-stage-6:
	poetry run python scripts/build_finetune_corpus.py --stage 6 -v

product-index:
	poetry run python scripts/build_product_index.py

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

eval:
	poetry run python scripts/eval_all.py

finetune:
	poetry run python finetuning/train_naija_reviewer.py --config finetuning/configs/naija_reviewer_qlora.yaml

paper:
	cd paper && pdflatex paper.tex && bibtex paper && pdflatex paper.tex && pdflatex paper.tex

test:
	poetry run pytest tests/ -v

lint:
	poetry run ruff check app/ tests/
	poetry run mypy app/ || true

format:
	poetry run black app/ tests/ finetuning/
	poetry run ruff format app/ tests/ finetuning/

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
