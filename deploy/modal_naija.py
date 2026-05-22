"""Serve NaijaReviewer-8B (Q4_K_M GGUF) on Modal as an OpenAI-compatible API.

Why Modal: serverless GPU, scales to zero (pay per use), gives an HTTPS endpoint.
The 8B Q4_K_M GGUF runs fine on a single L4 (24GB) — cheap and fast.

We serve with llama-cpp-python's built-in OpenAI-compatible server, so the app
calls it exactly like any OpenAI endpoint (/v1/chat/completions).

──────────────────────────────────────────────────────────────────────────────
DEPLOY
  pip install modal
  modal token new                       # one-time auth
  # HF token to pull the private repo (Modal's standard "huggingface" secret):
  modal secret create huggingface HF_TOKEN=hf_xxx
  modal deploy deploy/modal_naija.py

Modal prints a URL like:  https://<you>--naija-reviewer-serve.modal.run
Your OpenAI base URL is then:  https://<you>--naija-reviewer-serve.modal.run/v1

CALL IT (open endpoint, no auth)
  curl https://<you>--naija-reviewer-serve.modal.run/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"naija-reviewer-8b","messages":[{"role":"user","content":"Naija review of a Tecno phone"}]}'

WIRE INTO THE APP
  In .env:
    OPENAI_API_KEY=x        # any non-empty string; the endpoint is open
    OPENAI_BASE_URL=https://<you>--naija-reviewer-serve.modal.run/v1
    TASK1_BACKBONE=openai:naija-reviewer-8b
  (Or add a dedicated provider — ask and I'll wire it so it doesn't override
   the real OpenAI base.)
──────────────────────────────────────────────────────────────────────────────
"""

import os
import glob

import modal

HF_REPO = "Shinzmann/naija-reviewer-8b-v2-Q4_K_M-GGUF"
MODEL_DIR = "/models"
LCP_VERSION = "0.3.4"  # llama-cpp-python (CUDA wheel pinned below)

app = modal.App("naija-reviewer")

# Cache the downloaded GGUF in a Volume so cold starts don't re-download.
volume = modal.Volume.from_name("naija-gguf", create_if_missing=True)

image = (
    # CUDA *runtime* base so the prebuilt cu124 wheel finds libcudart.so.12.
    # (debian_slim has no CUDA libs -> "libcudart.so.12: cannot open shared object".)
    modal.Image.from_registry(
        "nvidia/cuda:12.4.1-runtime-ubuntu22.04", add_python="3.11"
    )
    # libgomp1 = GNU OpenMP runtime (libgomp.so.1) that libllama.so needs.
    .apt_install("libgomp1")
    .pip_install("huggingface_hub", "fastapi", "uvicorn")
    # Prebuilt CUDA 12.4 wheel for llama-cpp-python (GPU offload, no compile).
    .pip_install(
        f"llama-cpp-python[server]=={LCP_VERSION}",
        extra_index_url="https://abetlen.github.io/llama-cpp-python/whl/cu124",
    )
)


def _model_path() -> str:
    """Download the GGUF into the Volume (once) and return its path."""
    from huggingface_hub import snapshot_download

    local = snapshot_download(
        repo_id=HF_REPO,
        local_dir=MODEL_DIR,
        allow_patterns=["*.gguf"],
        token=os.environ.get("HF_TOKEN"),
    )
    ggufs = glob.glob(os.path.join(local, "**", "*.gguf"), recursive=True)
    if not ggufs:
        raise RuntimeError(f"no .gguf found in {HF_REPO}")
    return ggufs[0]


@app.function(
    image=image,
    gpu="L4",
    volumes={MODEL_DIR: volume},
    timeout=600,
    scaledown_window=300,         # scale to zero after 5 min idle
    # HF token to pull the private/gated repo. Uses Modal's standard
    # "huggingface" secret (key HF_TOKEN). If yours has a different name,
    # change it here.
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
# One request at a time per container (a single llama.cpp instance is not
# thread-safe); Modal scales out more containers under load.
@modal.concurrent(max_inputs=1)
@modal.asgi_app()
def serve():
    """Minimal OpenAI-compatible server built directly on llama_cpp.Llama.
    Avoids llama-cpp-python's bundled server (which throws
    "'coroutine' object is not callable" on some versions)."""
    from fastapi import FastAPI
    from pydantic import BaseModel
    from llama_cpp import Llama

    model_path = _model_path()
    volume.commit()  # persist the downloaded model

    llm = Llama(
        model_path=model_path,
        n_gpu_layers=-1,     # offload all layers to the GPU
        n_ctx=4096,
        chat_format="llama-3",
        verbose=False,
    )

    web = FastAPI()

    class ChatBody(BaseModel):
        messages: list
        max_tokens: int = 512
        temperature: float = 0.7
        stop: list[str] | None = None
        model: str | None = None

    @web.get("/v1/models")
    def models():
        return {"object": "list", "data": [{"id": "naija-reviewer-8b", "object": "model"}]}

    # sync def -> FastAPI runs it in a threadpool, so the event loop isn't blocked
    @web.post("/v1/chat/completions")
    def chat(body: ChatBody):
        return llm.create_chat_completion(
            messages=body.messages,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
            stop=body.stop,
        )

    return web
