"""
Modal deployment for Naija Persona Agent.

Deploy:
    modal deploy modal_deploy.py

Serve locally (dev):
    modal serve modal_deploy.py

Build the frontend first:
    cd frontend_v2 && npm run build && cd ..
"""

import modal

app = modal.App("naijapersona")

# ── Image ──────────────────────────────────────────────────────────────────────
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install_from_requirements("requirements.txt")
    # App source, data, and built frontend
    .add_local_dir("app",              remote_path="/app/app")
    .add_local_dir("data",             remote_path="/app/data")
    .add_local_dir("frontend_v2/dist", remote_path="/app/frontend_v2/dist")
)

# ── Web endpoint ───────────────────────────────────────────────────────────────
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("naija-persona-secrets")],
    allow_concurrent_inputs=50,
    timeout=300,
    # Uncomment to keep a warm container always running:
    # min_containers=1,
)
@modal.asgi_app()
def web():
    import sys
    sys.path.insert(0, "/app")
    from app.api.main import app as fastapi_application
    return fastapi_application
