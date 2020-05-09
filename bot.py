import apiai
import json
import requests
import random

from config import DIALOG_TOKEN, MY_KEY


class UserMessage:
    def __init__(self):
        self.game_flag = False
        self.score = 0
        self.pred_right = ""
        with open("quest.json", encoding='utf-8') as f:
            self.data = json.load(f)

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

    def mini_game(self, message):
        if len(self.data) != 0:
            num = random.randint(0, len(self.data) - 1)
            ask = self.data[num]["question"]
            answers = self.data[num]["answers"]
            right = self.data[num]["right"]

            if "игра" or "game" in message:
                self.game_flag = True
                answer = f"{ask}" \
                         f"{' '.join(answers)}"
                self.pred_right = right
            else:
                if self.pred_right == message:
                    answer = f"That's the right answer! {ask} {' '.join(answers)}"
                else:
                    answer = f"That's the wrong answer! {ask} {' '.join(answers)}"
                self.pred_right = right
            self.data.remove(self.data[num])
        else:
            if self.pred_right == message:
                answer = "That's the right answer!"
            else:
                answer = "That's the wrong answer!"
            answer += f"Your score is {self.score}/5"
            self.game_flag = False
            with open("quest.json", encoding='utf-8') as f:
                self.data = json.load(f)
        return answer

    def ask_bot(self, message):
        try:
            if "игра" in message.lower() or "game" in message.lower() or self.game_flag:
                answer = self.mini_game(message)
            else:
                answer = self.send_message(message)
            return answer
        except Exception as e:
            print(e)

    def translate_bot(self, ask, lang):
        answer = self.translate(ask, lang)
        return answer
