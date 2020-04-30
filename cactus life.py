import sqlalchemy
import requests
import datetime

from wtforms import FileField, SubmitField, StringField, PasswordField, BooleanField
from flask import Flask, render_template, url_for, redirect, request
from wtforms.validators import DataRequired
#from .db_session import SqlAlchemyBase
from flask_wtf import FlaskForm
from bs4 import BeautifulSoup

from config import API_KEY_NEWS, YANDEX_API, MY_KEY
from data import db_session
from data.users import User


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
param = []
activated = False

player = None



class AvatarForm(FlaskForm):
    file = FileField("Файл", validators=[DataRequired()])
    submit = SubmitField("Загрузить")


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('sign up')


def get_text(url):
    try:
        rs = requests.get(url)
        root = BeautifulSoup(rs.content, 'html.parser')
        article = root.select_one('article')
        return article.text
    except Exception:
        return 'No'

def translation(text):
    try:
        url = 'https://translate.yandex.net/api/v1.5/tr.json/translate?'
        key = MY_KEY
        lang = 'ru'
        r = requests.post(url, data={'key': key, 'text': text, 'lang': lang}).json()
        return r['text'][0]
    except Exception:
        return 'No'

def welcome():
    url_new = f'http://newsapi.org/v2/top-headlines?country=us&category=business&apiKey={API_KEY_NEWS}'
    url_new_1 = f'http://newsapi.org/v2/everything?q=apple&from=2020-04-23&to=2020-04-25&sortBy=popularity&apiKe={API_KEY_NEWS}'
    response = requests.get(url_new)
    response_1 = requests.get(url_new_1)
    if response and response_1:
        json_response = response.json()
        json_response_1 = response_1.json()
        news = []
        for i in range(max(len(json_response["articles"]), len(json_response_1["articles"]))):
            if i < len(json_response["articles"]):
                title = json_response["articles"][i]["title"]
                url = json_response["articles"][i]["url"]
                text = get_text(url)
                if text != 'No' and text.count('.') > 2:
                    text = translation(text)
                    if text != 'No':
                        news.append((translation(title), text))
            if i < len(json_response_1["articles"]):
                title = json_response_1["articles"][i]["title"]
                url = json_response_1["articles"][i]["url"]
                text = get_text(url)
                if text != 'No' and text.count('.') > 2:
                    text = translation(text)
                    if text != 'No':
                        news.append((translation(title), text))
        return news
    else:
        return [("Ошибка выполнения запроса", "упс")]


news = welcome()


@app.route('/')
@app.route('/index')
def index():
    return render_template('welcome_page.html', news=news)


@app.route('/indexing')
def indexing():
    return render_template('welcome_page_2.html', news=news)


@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    global activated, player, news
    if request.method == 'GET':
        return render_template('sign_up.html')
    elif request.method == 'POST':
        try:
            user = User()
            user.email = request.form['email']
            user.password = request.form['password']
            user.sex = request.form['sex']
            session = db_session.create_session()
            have = len([user.id for user in session.query(User)])
            session.add(user)
            have_now = len([user.id for user in session.query(User)])
            if have + 1 == have_now:
                player = user
                session.commit()
                return render_template('welcome_page_2.html', news=news)
            session.commit()
            return render_template('not_sign_up.html')
        except Exception as e:
            print(e)


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    global activated, player, news
    if request.method == 'GET':
        return render_template('sign_in.html')
    elif request.method == 'POST':
        try:
            em = request.form['email']
            p = request.form['password']
            session = db_session.create_session()
            for user in session.query(User):
                if user.email == em:
                    if user.password == p:
                        player = user
                        session.commit()
                        return render_template('welcome_page_2.html', news=news)
            session.commit()
            return render_template('not_sign_in.html')
        except Exception as e:
            print(e)


@app.route('/account', methods=['GET', 'POST'])
def account():
    global player
    form = AvatarForm()
    if form.validate_on_submit():
        avatar_path = f'static/img/ava_{form.file.data.filename}'
        form.file.data.save(avatar_path)
        session = db_session.create_session()
        for user in session.query(User):
            if user.email == player.email and user.password == player.password:
                user.img = avatar_path
                player = user
                break
        session.commit()
        if player.img is None:
            return render_template('account.html', user=player, f=False, form=form, avatar=avatar_path)
        else:
            return render_template('account.html', user=player, f=True, form=form)
    else:
        if player.img is None:
            return render_template('account.html', user=player, f=False, form=form)
        else:
            return render_template('account.html', user=player, f=True, form=form)


@app.route('/slides', methods=['GET', 'POST'])
def slides():
    param = {}
    param['slide1'] = url_for('static', filename='img/8.jpg')
    param['slide2'] = url_for('static', filename='img/1.jpg')
    param['slide3'] = url_for('static', filename='img/2.jpg')
    param['slide4'] = url_for('static', filename='img/3.jpg')
    param['slide5'] = url_for('static', filename='img/4.jpg')
    param['slide6'] = url_for('static', filename='img/5.jpg')
    param['slide7'] = url_for('static', filename='img/6.jpg')
    param['slide8'] = url_for('static', filename='img/7.jpg')
    return render_template('slides.html', **param)


@app.route('/loading', methods=['GET', 'POST'])
def loading():
    global param
    form = AvatarForm()
    if form.validate_on_submit():
        avatar_path = f'static/img/ava_{form.file.data.filename}'
        param.append(url_for('static', filename=f"img/ava_{form.file.data.filename}"))
        form.file.data.save(avatar_path)
        return render_template('load.html', form=form, p=param)
    return render_template('load.html', form=form)


if __name__ == '__main__':
    db_session.global_init("db/users.sqlite")
    app.run(port=8080, host='127.0.0.1')


#<a href="sign_up" class="btn btn-success btn-lg active" role="button" aria-pressed="true">Sign in</a>
#    <h1>♥</h1>
#    <a href="sign_up" class="btn btn-success btn-lg active" role="button" aria-pressed="true">Sign up</a>