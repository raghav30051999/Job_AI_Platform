import poplib
import email
import time
import datetime
import os
import json
from email.header import decode_header
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from utils.config import POP3_HOST, POP3_PORT, POP3_USER, POP3_PASS

STRAT_PATH = os.path.join("db", "pop3_strategy.json")


def _load_strategy():
    try:
        with open(STRAT_PATH, "r") as f:
            return tuple(json.load(f))
    except Exception:
        return None


def _save_strategy(s):
    try:
        os.makedirs("db", exist_ok=True)
        with open(STRAT_PATH, "w") as f:
            json.dump(list(s), f)
    except Exception:
        pass


def _decode_header(header):
    if not header:
        return ""
    out = []
    for part, charset in decode_header(header):
        if isinstance(part, bytes):
            out.append(part.decode(charset or "utf-8", errors="ignore"))
        else:
            out.append(part)
    return "".join(out)


def _html_to_text(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)
    except Exception:
        return html


def _get_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = str(part.get("Content-Disposition", ""))
            if "attachment" in cdisp:
                continue
            try:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                text = payload.decode(errors="ignore")
            except Exception:
                continue
            if ctype == "text/plain":
                body = text
                break
            elif ctype == "text/html" and not body:
                body = _html_to_text(text)
    else:
        try:
            payload = msg.get_payload(decode=True)
            body = payload.decode(errors="ignore") if payload else str(msg.get_payload())
            if msg.get_content_type() == "text/html":
                body = _html_to_text(body)
        except Exception:
            body = str(msg.get_payload())
    return body.strip()


def _connect_pop3():
    base_port = int(POP3_PORT or 995)
    strategies = [
        ("ssl", POP3_HOST, base_port),
        ("starttls", POP3_HOST, base_port),
        ("plain", POP3_HOST, base_port),
        ("ssl", "sandbox.pop3.mailtrap.io", 995),
        ("starttls", "sandbox.pop3.mailtrap.io", 1100),
        ("ssl", "pop3.mailtrap.io", 995),
        ("starttls", "pop3.mailtrap.io", 1100),
    ]
    cached = _load_strategy()
    if cached:
        strategies.insert(0, cached)      # restart → 1 attempt, no burst

    last_err = None
    for mode, host, port in strategies:
        if not host:
            continue
        time.sleep(0.5)                   # pace attempts
        try:
            if mode == "ssl":
                m = poplib.POP3_SSL(host, port, timeout=5)
            else:
                m = poplib.POP3(host, port, timeout=5)
                if mode == "starttls":
                    try:
                        m.stls()
                    except Exception:
                        pass
            m.user(POP3_USER)
            m.pass_(POP3_PASS)
            _save_strategy((mode, host, port))
            return m
        except Exception as e:
            last_err = e
    raise Exception(f"All POP3 strategies failed. Last: {last_err}")


def fetch_recent_emails(limit=10, since=None):
    mail = _connect_pop3()
    results = []
    try:
        count, _ = mail.stat()
        if count == 0:
            return []
        start = max(1, count - limit + 1)
        for num in range(count, start - 1, -1):
            _, lines, _ = mail.retr(num)
            time.sleep(0.1)
            raw = b"\r\n".join(lines)
            msg = email.message_from_bytes(raw)

            try:
                dt = parsedate_to_datetime(msg.get("Date", ""))
                if dt.tzinfo is not None:
                    dt = dt.astimezone(tz=None).replace(tzinfo=None)  # naive local
            except Exception:
                dt = datetime.datetime.now()

            # ---- "scan from today" filter ----
            if since is not None and dt < since:
                continue

            results.append({
                "message_id": msg.get("Message-ID", f"pop3-{num}"),
                "subject": _decode_header(msg.get("Subject", "")),
                "sender": _decode_header(msg.get("From", "")),
                "date": dt.strftime("%Y-%m-%d %H:%M"),
                "_dt": dt,
                "body": _get_body(msg)[:3000],
            })
    finally:
        try:
            mail.quit()
        except Exception:
            pass
    return results