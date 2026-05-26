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
    .apt_install("git", "libpq-dev", "gcc")
    # copy=True bakes files into the image at build time (required before run_commands)
    .add_local_file("requirements.txt", "/tmp/requirements.txt", copy=True)
    .run_commands("pip install --no-cache-dir -r /tmp/requirements.txt")
    # Bake app source, data, and built frontend directly into the image
    # so StaticFiles can find /app/frontend_v2/dist/assets/ at startup
    .add_local_dir("app",              remote_path="/app/app",              copy=True)
    .add_local_dir("data",             remote_path="/app/data",             copy=True)
    .add_local_dir("frontend_v2/dist", remote_path="/app/frontend_v2/dist", copy=True)
)

# ── Web endpoint ───────────────────────────────────────────────────────────────
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("naija-persona-secrets")],
    timeout=300,
)
@modal.concurrent(max_inputs=50)
@modal.asgi_app()
def web():
    import sys
    sys.path.insert(0, "/app")
    from app.api.main import app as fastapi_application
    return fastapi_application
