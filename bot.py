import apiai
import json
import requests

from config import DIALOG_TOKEN, MY_KEY


class UserMessage:
    def __init__(self):
        pass

    def send_message(self, message):
        request = apiai.ApiAI(DIALOG_TOKEN).text_request()
        request.lang = "ru"
        request.session_id = "sessiong_1"
        request.query = message
        response = json.loads(request.getresponse().read().decode("utf-8"))
        return response["result"]["fulfillment"]["speech"]

    def translate(self, ask, lang):
        try:
            get = f"https://translate.yandex.net/api/v1.5/tr.json/translate?lang={lang}" \
                  f"&key={MY_KEY}&text={ask}"
            response = requests.get(get)
            json_response = response.json()
            answer = json_response["text"][0]
            return answer
        except Exception as e:
            print(e)


def ask_bot(message):
    answer = UserMessage().send_message(message)
    return answer


def translate_bot(ask, lang):
    answer = UserMessage().translate(ask, lang)
    return answer

