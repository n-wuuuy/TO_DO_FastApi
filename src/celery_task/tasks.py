import smtplib
from email.message import EmailMessage

from celery import Celery

from src.config import REDIS_HOST, REDIS_PORT, SMTP_USER, SMTP_PASSWORD

celery = Celery('tasks', broker=f'redis://{REDIS_HOST}:{REDIS_PORT}')

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def get_email_template_dashboard(user_email: str, data: list):
    email = EmailMessage()
    email['Subject'] = 'You Tasks'
    email['From'] = SMTP_USER
    email['To'] = user_email
    print(data)
    email.set_content(
        '<div>'
        f'<h1 style="color: red;">Здравствуйте, {data}, а вот и ваш отчет. Зацените 😊</h1>'
        '</div>',
        subtype='html'
    )
    return email


@celery.task
def send_email_report_dashboard(user_email: str, data: list):
    email = get_email_template_dashboard(user_email, data)
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(email)
