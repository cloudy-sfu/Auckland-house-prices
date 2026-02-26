import logging

import requests


class TelegramHandler(logging.Handler):
    """
    A logging handler that sends log records to a Telegram group via Bot API.

    Ref: https://core.telegram.org/bots/api#sendmessage
    """

    def __init__(self, bot_token: str = None, chat_id: str = None, level=logging.NOTSET):
        super().__init__(level)

        if bot_token and chat_id:
            self._enabled = True
            self._url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            self._chat_id = chat_id
        else:
            self._enabled = False

    def emit(self, record):
        if not self._enabled:
            return

        try:
            message = self.format(record)
            # Ref: https://core.telegram.org/bots/api#sendmessage
            payload = {
                "chat_id": self._chat_id,
                "text": message,
                "parse_mode": "HTML",
            }
            response = requests.post(self._url, data=payload, timeout=10)
            response.raise_for_status()

        except (requests.ConnectionError, requests.Timeout):
            return

        except Exception:
            self.handleError(record)

    def handleError(self, record):
        self._enabled = False
        try:
            err_logger = logging.getLogger(record.name)
            err_logger.error(
                f"TelegramHandler unexpected error while emitting: {record.getMessage()}"
            )
        finally:
            self._enabled = True
            raise
