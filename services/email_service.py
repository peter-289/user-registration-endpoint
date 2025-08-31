from fastapi_mail import FastMail, MessageSchema
from config import mail_config
from jinja2 import Environment, FileSystemLoader

async def send_verification_email(email: str, token: str):
    verification_link = f"http://127.0.0.1:8000/users/verify?token={token}"

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("email_templates/verify_email.html")
    body = template.render(email=email, verification_link=verification_link)

    message = MessageSchema(
        subject="Verify your Tech Pulse account",
        recipients=[email],
        cc=["support@techpulse.com"],
        bcc=["audit@techpulse.com"],
        reply_to=["noreply@techpulse.com"],
        body=body,
        subtype="html"
)

    ##Send the email
    print(f"Verification email queued for {email} with token {token}")

    fm = FastMail(mail_config)
    await fm.send_message(message)

    