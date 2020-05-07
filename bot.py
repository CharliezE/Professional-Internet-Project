import apiai
import json

from config import SMALL_TALK__TOKEN, TRANSLATE_TOKEN, DIALOG_TOKEN


class UserMessage:
    def __init__(self):
        pass

    def send_message(self, message):
        self.request = apiai.ApiAI(DIALOG_TOKEN).text_request()
        self.request.lang = "ru"
        self.request.session_id = "sessiong_1"
        self.request.query = message
        response = json.loads(self.request.getresponse().read().decode("utf-8"))
        return response["result"]["fulfillment"]["speech"]


def ask_bot(message):
    answer = UserMessage().send_message(message)
    return answer

