
import random
import smtplib
from email.message import EmailMessage
import ssl
import os

my_email = os.environ.get("MY_EMAIL")
my_pass = os.environ.get("MY_PASS")
email_receiver = "nathanflores887@gmail.com"

em = EmailMessage()
em["From"] = my_email
em["Subject"] = "Someone Sent you a message from your Website!"
em.set_content(body)
context = ssl.create_default_context()


def send_email(name, email, phone_num, message):
    em = EmailMessage()
    em["From"] = MY_EMAIL
    em["Subject"] = "Someone Sent you a message from your Website!"
    em.set_content(f"Name: {name}\nEmail: {email}\nPhone Number: {phone_num}\n\nMessage:\n{message}")
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as connection:
        connection.login(MY_EMAIL, MY_PASS)
        connection.sendmail(my_email,
                            email_receiver,
                            em.as_string()
                            )


for email in email_receiver:
    send_email(email)