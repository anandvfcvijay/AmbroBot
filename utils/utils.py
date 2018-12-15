import logging

import os
from requests import ReadTimeout
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


# Generic utils
def monospace(text):
    return f'```\n{text}\n```'


def normalize(text, limit=11, trim_end='.'):
    """Trim and append . if text is too long. Else return it unmodified"""
    return f'{text[:limit]}{trim_end}' if len(text) > limit else text


def soupify_url(url, timeout=2, encoding='utf-8', **kwargs):
    """Given a url returns a BeautifulSoup object"""
    try:
        r = requests.get(url, timeout=timeout, **kwargs)
    except ReadTimeout:
        logger.info("[soupify_url] Request for %s timed out.", url)
        raise

    r.raise_for_status()
    r.encoding = encoding
    if r.status_code == 200:
        return BeautifulSoup(r.text, 'lxml')
    else:
        raise ConnectionError(
            f'{url} returned error status %s - ', r.status_code, r.reason
        )


def error_handler(bot, update, error):
    try:
        raise error
    except Unauthorized:
        logger.info("User unauthorized")
    except BadRequest as e:
        msg = getattr(error, 'message', None)
        if msg is None:
            raise
        if msg == 'Query_id_invalid':
            logger.info("We took too long to answer.")
        elif msg == 'Message is not modified':
            logger.info(
                "Tried to edit a message but text hasn't changed."
                " Probably a button in inline keyboard was pressed but it didn't change the message"
            )
        else:
            logger.info("Bad Request exception: %s", msg)

    except TimedOut:
        logger.info("Request timed out")
        bot.send_message(
            chat_id=update.effective_message.chat_id, text='The request timed out ⌛️'
        )

    except TelegramError:
        logger.exception("A TelegramError occurred")

    finally:
        if hasattr(update, 'to_dict'):
            logger.info(f"Conflicting update: '{update.to_dict()}'")
        else:
            logger.info('Error found: %s. Update: %s', error, update)


def send_message_to_admin(bot, message, **kwargs):
    bot.send_message(chat_id=os.environ['ADMIN_ID'], text=message, **kwargs)
