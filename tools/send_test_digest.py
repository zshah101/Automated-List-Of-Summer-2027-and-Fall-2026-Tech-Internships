"""Preview or test-send the daily email digest without waiting for a real run.

    python tools/send_test_digest.py                       # write digest_preview.html
    python tools/send_test_digest.py --send you@x.com      # actually send one email

Preview mode needs no credentials: it composes today's digest from data/jobs.json
(falling back to the newest open roles when nothing is fresh) and writes
digest_preview.html next to this script — open it in a browser.

Send mode uses the same env vars as production (BREVO_API_KEY, MAIL_FROM) and
sends ONLY to the address you pass — it never touches the subscriber list and
never updates data/mail_state.json, so the real daily digest is unaffected.
"""

from __future__ import annotations

import os
import sys

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from intern_engine import mailer, paths, store  # noqa: E402


def main() -> None:
    data = store.load(paths.JOBS_PATH)
    fresh = mailer.new_roles(data)
    if not fresh:
        # Nothing new in the window — preview with the newest open roles instead.
        fresh = sorted(
            (r for r in data.values() if r.get("is_open")),
            key=lambda r: r.get("first_seen_at") or "", reverse=True,
        )[:10]
        print(f"(no roles in the news window; previewing the {len(fresh)} newest open roles)")
    if not fresh:
        print("Store has no open roles at all — run `python run.py update` first.")
        sys.exit(1)

    html = mailer.build_digest_html(fresh).replace("{{UNSUB_URL}}", "#test-no-unsub")
    subject = f"[TEST] {len(fresh)} new internship{'s' if len(fresh) != 1 else ''}"

    if "--send" in sys.argv:
        try:
            to_addr = sys.argv[sys.argv.index("--send") + 1]
        except IndexError:
            print("Usage: python tools/send_test_digest.py --send you@example.com")
            sys.exit(1)
        api_key = os.environ.get("BREVO_API_KEY")
        sender = mailer._sender()  # noqa: SLF001 — same package's tool
        if not api_key or not sender:
            print("Set BREVO_API_KEY and MAIL_FROM (verified sender) to test-send.")
            sys.exit(1)
        resp = httpx.post(
            mailer._BREVO_URL,  # noqa: SLF001
            headers={"api-key": api_key, "Content-Type": "application/json"},
            json={"sender": sender, "to": [{"email": to_addr}],
                  "subject": subject, "htmlContent": html},
            timeout=20,
        )
        print(f"Brevo responded {resp.status_code}: {resp.text[:300]}")
        resp.raise_for_status()
        print(f"Test digest sent to {to_addr}.")
    else:
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "digest_preview.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Digest preview ({len(fresh)} roles) -> {out}")
        print("Pass --send you@example.com to send a real test email via Brevo.")


if __name__ == "__main__":
    main()
