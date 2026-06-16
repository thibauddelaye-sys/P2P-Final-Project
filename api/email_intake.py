"""email_intake.py — pull invoice attachments from a dedicated mailbox over IMAP.

Designed for the p2p-inventory tool: a "Check inbox" action calls fetch_invoice_attachments(),
then each attachment is run through the existing LLM extraction (/api/extract logic).

Standalone connection test (run this FIRST to verify Gmail works, before wiring the UI):
    set IMAP_USER=maisonlumiere.invoices@gmail.com        (PowerShell: $env:IMAP_USER="...")
    set IMAP_PASSWORD=your-16-char-app-password
    python email_intake.py
It prints how many invoice attachments it found and their filenames — never the content.

Env vars used:
    IMAP_HOST      (default imap.gmail.com)
    IMAP_USER      the dedicated mailbox address
    IMAP_PASSWORD  a Google *app password* (not the account password)
"""
from __future__ import annotations
import email, imaplib, os
from email.header import decode_header

ATTACH_EXT = (".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff")

def _decode(value: str | None) -> str:
    if not value:
        return ""
    out = []
    for text, enc in decode_header(value):
        out.append(text.decode(enc or "utf-8", "ignore") if isinstance(text, bytes) else text)
    return "".join(out)

def fetch_invoice_attachments(host: str, user: str, password: str,
                              folder: str = "INBOX", only_unseen: bool = True,
                              mark_seen: bool = True) -> list[dict]:
    """Return a list of {filename, content(bytes), from, subject} for invoice-like attachments.

    only_unseen=True processes just new mail; mark_seen=True flags them read so the next
    poll doesn't reprocess them. Raises on auth/connection errors (surface them to the user).
    """
    M = imaplib.IMAP4_SSL(host)
    try:
        M.login(user, password)
        M.select(folder)
        typ, data = M.search(None, "(UNSEEN)" if only_unseen else "(ALL)")
        results: list[dict] = []
        for num in data[0].split():
            typ, msg_data = M.fetch(num, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            sender, subject = _decode(msg.get("From")), _decode(msg.get("Subject"))
            msg_id = _decode(msg.get("Message-ID"))
            had_attachment = False
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                fn = part.get_filename()
                if fn and _decode(fn).lower().endswith(ATTACH_EXT):
                    payload = part.get_payload(decode=True)
                    if payload:
                        results.append({"filename": _decode(fn), "content": payload,
                                        "from": sender, "subject": subject, "msg_id": msg_id})
                        had_attachment = True
            if mark_seen and had_attachment:
                M.store(num, "+FLAGS", "\\Seen")
        return results
    finally:
        try: M.logout()
        except Exception: pass

if __name__ == "__main__":
    host = os.getenv("IMAP_HOST", "imap.gmail.com")
    user = os.getenv("IMAP_USER"); pwd = os.getenv("IMAP_PASSWORD")
    if not user or not pwd:
        print("Set IMAP_USER and IMAP_PASSWORD env vars first."); raise SystemExit(1)
    print(f"Connecting to {host} as {user} …")
    try:
        items = fetch_invoice_attachments(host, user, pwd, only_unseen=False, mark_seen=False)
    except imaplib.IMAP4.error as e:
        print(f"❌ IMAP login/select failed: {e}")
        print("   Checklist: 2-Step Verification ON · using an APP PASSWORD · IMAP enabled in Gmail.")
        raise SystemExit(1)
    print(f"✅ Connected. Found {len(items)} invoice attachment(s):")
    for it in items:
        print(f"   • {it['filename']}   (from: {it['from'][:40]})")
    print("(content not shown — connection test only)")
