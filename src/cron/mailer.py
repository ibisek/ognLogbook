
import json
import os

from redis import StrictRedis

import configuration    # just to read the values into memory when running standalone
from configuration import redisConfig
from cron.eventWatcher.sendMail3 import SendMail3


class Mailer:
    RUN_INTERVAL = 60  # [s]
    REDIS_Q_KEY = 'mailQ'
    NUM_MAILS_IN_BATCH = 2

    def __init__(self):
        print(f"[INFO] Mailer scheduled to run every {self.RUN_INTERVAL}s.")
        self.redis = StrictRedis(**redisConfig)
        self.sendMail = SendMail3(**os.environ)

    def __del__(self):
        print('Mailer quit.')

    def enqueue(self, recipient: str, subject: str, body: str, attachment: str = None):
        d = {
            'to': recipient,
            'subj': subject,
            'body': body,
            'att': attachment,
        }
        j = json.dumps(d, indent=None)
        self.redis.rpush(self.REDIS_Q_KEY, j)

    def processMailQueue(self):
        i = 0
        while j := self.redis.lpop(self.REDIS_Q_KEY):
            d = json.loads(j)

            receiver_email = d.get('to', None)
            subject = d.get('subj', None)
            body = d.get('body', None)
            attachment = d.get('att', None)

            if not receiver_email or not subject or not body:
                continue

            try:
                self.sendMail.sendMail(receiver_email=receiver_email, subject=subject, text=body, attachment=attachment)
            except Exception as e:
                print('[ERROR] mailer.processQueue: {}'.format(e))
                self.redis.rpush(j)

            i += 1
            if i >= self.NUM_MAILS_IN_BATCH:
                break


if __name__ == '__main__':
    redis = StrictRedis(**redisConfig)

    m = Mailer()

    recipient = '**@centrum.cz'
    subject = 'Pokusny mail #{}'
    body = 'Toto je nejaky text v mailu.'

    for i in range(2):
        m.enqueue(recipient=recipient, subject=subject.format(i), body=body)

    m.processMailQueue()
