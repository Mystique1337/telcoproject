"""Email notifications via Resend API (stdlib urllib — no extra deps)."""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


def send_run_complete_email(
    to_email: str,
    project_name: str,
    run_id: str,
    avg_rating: float | None,
    buy_likelihood: float | None,
    n_personas: int,
    themes_praised: list[str],
) -> None:
    """Send a panel-complete notification email via Resend.

    No-ops if RESEND_API_KEY is not configured or if to_email is empty.
    All exceptions are caught and logged — this must never raise.
    """
    try:
        from app.config import get_settings
        settings = get_settings()

        if not settings.resend_api_key:
            logger.info("Resend API key not configured — skipping email for run %s", run_id)
            return

        if not to_email:
            logger.info("No recipient email — skipping email for run %s", run_id)
            return

        run_url = f"{settings.app_base_url}/runs/{run_id}"

        rating_str = f"{avg_rating:.1f} / 5" if avg_rating is not None else "N/A"
        buy_str = f"{buy_likelihood}%" if buy_likelihood is not None else "N/A"
        themes_html = "".join(
            f'<span style="display:inline-block;margin:2px 4px 2px 0;padding:3px 10px;background:#052e16;border:1px solid #14532d;border-radius:999px;color:#4ade80;font-size:13px;">{t}</span>'
            for t in (themes_praised or [])[:6]
        )
        if not themes_html:
            themes_html = "<span style='color:#6b7280;font-size:13px;'>No theme data</span>"

        html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Panel complete: {project_name}</title></head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:'Inter',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#111111;border:1px solid #1f2937;border-radius:16px;overflow:hidden;">
        <!-- Header -->
        <tr>
          <td style="background:#052e16;padding:28px 36px;border-bottom:1px solid #14532d;">
            <table cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:#16a34a;width:32px;height:32px;border-radius:8px;text-align:center;vertical-align:middle;">
                  <span style="color:white;font-weight:700;font-size:14px;">NP</span>
                </td>
                <td style="padding-left:10px;">
                  <span style="color:#f0fdf4;font-weight:700;font-size:15px;">Naija Persona</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:36px 36px 28px;">
            <h1 style="margin:0 0 6px;color:#f9fafb;font-size:22px;font-weight:700;">Panel complete</h1>
            <p style="margin:0 0 24px;color:#6b7280;font-size:14px;">
              Your <strong style="color:#d1fae5;">{project_name}</strong> panel has finished running across {n_personas} Nigerian consumer personas.
            </p>

            <!-- Stat cards -->
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
              <tr>
                <td width="48%" style="background:#1a1a1a;border:1px solid #1f2937;border-radius:12px;padding:16px 20px;text-align:center;">
                  <div style="color:#fbbf24;font-size:26px;font-weight:700;">{rating_str}</div>
                  <div style="color:#9ca3af;font-size:12px;margin-top:4px;">Avg Rating</div>
                </td>
                <td width="4%"></td>
                <td width="48%" style="background:#1a1a1a;border:1px solid #1f2937;border-radius:12px;padding:16px 20px;text-align:center;">
                  <div style="color:#4ade80;font-size:26px;font-weight:700;">{buy_str}</div>
                  <div style="color:#9ca3af;font-size:12px;margin-top:4px;">Buy Likelihood</div>
                </td>
              </tr>
            </table>

            <!-- Themes -->
            <div style="margin-bottom:28px;">
              <p style="color:#9ca3af;font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin:0 0 10px;">Top praised themes</p>
              <div>{themes_html}</div>
            </div>

            <!-- CTA -->
            <a href="{run_url}" style="display:inline-block;background:#16a34a;color:#fff;font-weight:600;font-size:14px;padding:13px 28px;border-radius:10px;text-decoration:none;">
              View full results →
            </a>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:20px 36px;border-top:1px solid #1f2937;">
            <p style="margin:0;color:#374151;font-size:12px;">
              You received this because you ran a panel on <a href="{settings.app_base_url}" style="color:#4ade80;text-decoration:none;">Naija Persona</a>.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

        payload = json.dumps({
            "from": "InsideNaija <noreply@naijapersona.com>",
            "to": [to_email],
            "subject": f"Panel complete: {project_name}",
            "html": html_body,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info(
                "Email sent for run %s to %s (status %s)", run_id, to_email, resp.status
            )

    except Exception as exc:
        logger.warning("Failed to send email for run %s: %s", run_id, exc)
