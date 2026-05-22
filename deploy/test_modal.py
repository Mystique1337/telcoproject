"""Quick test for the Modal-hosted NaijaReviewer endpoint.

Usage:
  python deploy/test_modal.py https://<you>--naija-reviewer-serve.modal.run
  # or set MODAL_BASE_URL and run with no arg:
  MODAL_BASE_URL=https://<you>--naija-reviewer-serve.modal.run python deploy/test_modal.py

The endpoint is OpenAI-compatible, so this hits /v1/chat/completions.
First call after idle includes a cold start (model download/load) — give it ~60s.
"""

import os
import sys
import time

import httpx


def test_modal(base_url: str, prompt: str | None = None, api_key: str = "x") -> None:
    base = base_url.rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    prompt = prompt or (
        "You are Chinwe, a code-mixed Owerri shopper. Write a short, authentic "
        "Jumia review of an Oraimo wireless earbud you bought."
    )

    print(f"→ {base}/chat/completions")
    # 1) list models (sanity)
    try:
        with httpx.Client(timeout=120) as c:
            m = c.get(f"{base}/models", headers={"Authorization": f"Bearer {api_key}"})
            if m.status_code == 200:
                ids = [x.get("id") for x in m.json().get("data", [])]
                print(f"  models: {ids}")
    except Exception as e:  # noqa: BLE001
        print(f"  (models check skipped: {e})")

    # 2) chat completion
    t = time.time()
    try:
        with httpx.Client(timeout=180) as c:
            r = c.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "naija-reviewer-8b",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                    "temperature": 0.7,
                },
            )
    except Exception as e:  # noqa: BLE001
        print(f"✗ request failed: {e}")
        return

    dt = time.time() - t
    print(f"  HTTP {r.status_code}  ({dt:.1f}s)")
    if r.status_code != 200:
        print(r.text[:500])
        return
    data = r.json()
    msg = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    print("\n--- model output ---")
    print(msg.strip())
    print(f"\ntokens: {usage}")
    print("✓ endpoint is live")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("MODAL_BASE_URL")
    if not url:
        print("Pass the Modal URL as an arg or set MODAL_BASE_URL.\n"
              "  python deploy/test_modal.py https://<you>--naija-reviewer-serve.modal.run")
        sys.exit(1)
    test_modal(url, prompt=sys.argv[2] if len(sys.argv) > 2 else None)
