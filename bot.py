import apiai
import json

SMALL_TALK__TOKEN = "b9a3d18a3b424574aae740c634dc22a5"
TRANSLATE_TOKEN = "76bf72f4c5354992b9edbf8a02f5b165"


class UserMessage:
    def __init__(self):
        pass

    def send_message(self, message):
        self.request = apiai.ApiAI(SMALL_TALK__TOKEN).text_request()
        self.request.lang = "ru"
        self.request.session_id = "sessiong_1"
        self.request.query = message
        response = json.loads(self.request.getresponse().read().decode("utf-8"))
        return response["result"]["fulfillment"]["speech"]


def ask_bot(message):
    answer = UserMessage().send_message(message)
    return answer

