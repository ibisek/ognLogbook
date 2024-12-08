"""
https://pypi.org/project/emails/
https://python-emails.readthedocs.io/en/latest/
https://realpython.com/python-send-email/
"""
import ssl
import smtplib

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header


class SendMail3:
    # host = 'smtp.centrum.cz'
    # port = 587
    # user = 'ognlogbook@centrum.cz'
    # password = '**'
    # sender_email = 'ognlogbook@centrum.cz'

    def __init__(self, **config):
        self.host = config.get('MAIL_HOST', None)
        self.port = int(config.get('MAIL_PORT', None))
        self.user = config.get('MAIL_USER', None)
        self.password = config.get('MAIL_PASSWORD', None)
        self.sender_email = config.get('MAIL_FROM', None)

    def sendMail(self, receiver_email, subject, text, attachment: str = None):
        # body = f"From:Automat\nSubject:{subject}\n\n{body}"

        if not attachment:
            # text = f"Subject:{subject}\n\n{text}"
            msg = MIMEMultipart('alternative')
            msg.set_charset('utf8')
            msg['FROM'] = self.sender_email
            msg['TO'] = receiver_email
            msg['Subject'] = Header(subject.encode('utf-8'), 'UTF-8').encode()
            msg.attach(MIMEText(text, "plain"))
            text = msg.as_string()

        else:
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = receiver_email
            message["Subject"] = subject
            # message["Bcc"] = receiver_email  # Recommended for mass emails

            message.attach(MIMEText(text, "plain"))

            part = MIMEBase("application", "json")
            part.set_payload(attachment)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename=data.json",
            )
            message.attach(part)
            text = message.as_string()

        try:
            context = ssl.create_default_context()

            if self.port == 587:
                with smtplib.SMTP(self.host, self.port) as server:
                    # server.ehlo()  # Can be omitted
                    server.starttls(context=context)
                    # server.ehlo()  # Can be omitted
                    server.login(self.user, self.password)
                    server.sendmail(self.sender_email, receiver_email, text)

            elif self.port == 993:
                with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
                    server.login(self.sender_email, self.password)
                    res = server.sendmail(self.sender_email, receiver_email, text)
                    print('res:', res)

            else:
                raise ValueError(f'Unsupported port {self.port}!')

        except smtplib.SMTPAuthenticationError as e:
            # print('[ERROR]', e)
            raise e

        except smtplib.SMTPConnectError as e:
            # print('[ERROR]', e)
            raise e

