

# 3rd party
from marrow.mailer import Mailer, Message

# local
import lib.logconfig


LOG = lib.logconfig.app_log


"""
cbjewelz got this working:

 i did get it working with gmail though, i made the settings:
    mailer = Mailer(
        dict(
            transport=dict(
                use='smtp',
                host='smtp.gmail.com',
                port = '587',
                username = 'email',
                password = 'password',
                tls = 'required')))

    you have to create a special App password through google if you have 2FA enabled
"""

def send(subject, text, html, sender, recipient, cc=None, bcc=None):

    mailer = Mailer(
        dict(
            transport=dict(
                use='smtp',
                host='localhost')))

    mailer.start()

    message = Message(
        author=sender,
        to=recipient,
        cc=cc,
        bcc=bcc
    )

    message.subject = subject
    message.rich = html
    message.plain = text

    mailer.send(message)
    mailer.stop()

def notify_admin(msg, sys_config):

    LOG.debug("Notifying admin about {}".format(msg))

    subject = "SurgeTraderBOT aborted execution on exception"
    sender = sys_config.email_sender
    recipient = sys_config.email_bcc
    send(subject,
                 text=msg, html=None,
                 sender=sender,
                 recipient=recipient,
                 bcc=None
                 )
