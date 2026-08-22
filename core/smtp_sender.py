import smtplib
import uuid
import datetime
import time
from email.mime.text import MIMEText
from utils.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
from email.utils import format_datetime

LAST_SEND = {"time": 0.0}
MIN_INTERVAL = 3.0


def send_test_email(subject: str, from_label: str, body: str):
    now = time.time()
    if now - LAST_SEND["time"] < MIN_INTERVAL:
        wait = int(MIN_INTERVAL - (now - LAST_SEND["time"])) + 1
        raise Exception(f"Please wait {wait}s before sending again (rate limit protection).")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_label
    msg["To"] = "candidate@demo-job-tracker.com"
    msg["Message-ID"] = f"<{uuid.uuid4().hex}@demo-job-tracker.com>"
    msg["Date"] = format_datetime(datetime.datetime.now().astimezone())

    for attempt in range(3):
        try:
            with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, ["candidate@demo-job-tracker.com"], msg.as_string())
            LAST_SEND["time"] = time.time()
            return
        except smtplib.SMTPDataError as e:
            if "too many" in str(e).lower() and attempt < 2:
                time.sleep(5 * (2 ** attempt))   # 5s, 10s backoff
                continue
            raise Exception(f"SMTP rate limit. Wait 10-20s and try again. Details: {e}")
        except Exception as e:
            raise Exception(f"Failed to send: {e}")