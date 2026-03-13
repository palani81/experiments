import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def send_to_kindle(pdf_path: str, kindle_email: str, smtp_host: str, smtp_port: int,
                   smtp_user: str, smtp_password: str, smtp_use_tls: bool = True,
                   subject: str = "Crossword") -> bool:
    """Send a PDF to Kindle via email. All settings passed explicitly (from DB or config)."""
    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = kindle_email
    msg["Subject"] = subject
    msg.attach(MIMEText("", "plain"))

    pdf_data = Path(pdf_path).read_bytes()
    attachment = MIMEApplication(pdf_data, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=Path(pdf_path).name)
    msg.attach(attachment)

    if smtp_port == 465:
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
    else:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
        if smtp_use_tls:
            server.starttls()

    server.login(smtp_user, smtp_password)
    server.send_message(msg)
    server.quit()
    return True


def send_test_email(kindle_email: str, smtp_host: str, smtp_port: int,
                    smtp_user: str, smtp_password: str, smtp_use_tls: bool = True) -> bool:
    """Send a test email to verify SMTP configuration."""
    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = kindle_email
    msg["Subject"] = "Kindle Crossword - Test"
    msg.attach(MIMEText("This is a test email from Kindle Crossword app.", "plain"))

    if smtp_port == 465:
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
    else:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
        if smtp_use_tls:
            server.starttls()

    server.login(smtp_user, smtp_password)
    server.send_message(msg)
    server.quit()
    return True
