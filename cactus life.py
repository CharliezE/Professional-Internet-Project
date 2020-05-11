import requests
import random
import pickle

from datetime import datetime
from wtforms import FileField, SubmitField
from flask import Flask, render_template, url_for, redirect, request
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from bs4 import BeautifulSoup

from bot import UserMessage

from config import API_KEY_NEWS, YANDEX_API, MY_KEY, MUSIC_KEY
from data import db_session
from data.users import User


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
GENRE = ['Instrumental', 'Classical', 'Electronic', 'Latin', 'Hip hop', 'Country',
         'Metal', 'Reggae', 'Blues', 'Folk', 'Jazz', 'Pop', 'Rock', 'Ska']

player = None
bot_dialog = []
bot_message = UserMessage()
dialog = None
buddy = None


class AvatarForm(FlaskForm):
    file = FileField("Файл", validators=[DataRequired()])
    submit = SubmitField("Загрузить")


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


def check(e, p):
    em = e.split('@')[1]
    if e.count('@') == 1 and len(em[0]) > 0 and em.count('.') == 1:
        eml = em.split('.')
        if len(eml[0]) > 0 and len(eml[1]) > 0:
            if len(''.join(p.split())) > 8 and ' ' not in p:
                return True
    return False


def welcome():
    url_new = f'http://newsapi.org/v2/top-headlines?sources=techcrunch&apiKey={API_KEY_NEWS}'
    response = requests.get(url_new)
    if response:
        json_response = response.json()
        news = []
        for i in range(len(json_response["articles"])):
            title = json_response["articles"][i]["title"]
            url = json_response["articles"][i]["url"]
            text = get_text(url)
            if text != 'No' and text.count('.') > 2:
                text = translation(text)
                if text != 'No':
                    news.append((translation(title), text))
        return news
    else:
        return [("Ошибка выполнения запроса", "упс")]


def get_music(genre):
    url_new = f'https://api.jamendo.com/v3.0/playlists/tracks/?client_id={MUSIC_KEY}' \
              f'&format=jsonpretty&limit=50&name={genre}&track_type=albumtrack'
    response = requests.get(url_new)
    all_music = []
    if response:
        json_response = response.json()
        for x in json_response["results"]:
            for y in x['tracks']:
                artist = y['artist_name']
                title = y['name']
                img = y['image'].replace('\/', '/')
                song = y['audio'].replace('\/', '/')
                all_music.append((artist, title, img, song))
    return all_music


news = welcome()


@app.route('/')
@app.route('/index')
def index():
    return render_template('welcome_page.html', news=news)


@app.route('/indexing')
def indexing():
    global buddy
    buddy = None
    return render_template('welcome_page_2.html', news=news)


@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    global player, news
    if request.method == 'GET':
        return render_template('sign_up.html')
    elif request.method == 'POST':
        try:
            em = request.form['email']
            p = request.form['password']
            if check(em, p):
                user = User()
                user.email = em
                user.password = p
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
    global player, news
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
    global player, buddy
    buddy = None
    form = AvatarForm()
    name = player.email.split('@')[0]
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
            return render_template('account.html', user=player, f=False, form=form, avatar=avatar_path, name=name.capitalize())
        else:
            return render_template('account.html', user=player, f=True, form=form, name=name.capitalize())
    else:
        if player.img is None:
            return render_template('account.html', user=player, f=False, form=form, name=name.capitalize())
        else:
            return render_template('account.html', user=player, f=True, form=form, name=name.capitalize())


@app.route('/exit', methods=['GET', 'POST'])
def exit():
    global player, bot_dialog, dialog, buddy
    player = None
    bot_dialog = []
    with open('dialogs.pickle', 'wb') as f:
        pickle.dump(dialog, f)
    buddy = None
    dialog = None
    return render_template('welcome_page.html', news=news)


@app.route('/help', methods=['GET', 'POST'])
def help():
    return render_template('help.html')


@app.route("/bot", methods=["GET", "POST"])
def bot():
    global bot_dialog, buddy
    buddy = None
    if request.method == "GET":
        name = player.email.split('@')[0]
        return render_template('bot.html', dlg=bot_dialog[::-1], name=name.capitalize())
    elif request.method == "POST":
        try:
            t = str(datetime.today()).split()
            time = t[1][:-10] + ' ' + '.'.join(t[0].split('-')[::-1])
            ask = request.form['ask']
            answer = bot_message.ask_bot(ask)
            name = player.email.split('@')[0]
            bot_dialog.append((True, ask, time))
            bot_dialog.append((False, answer, time))
            return render_template('bot.html', dlg=bot_dialog[::-1], name=name.capitalize(), time=time)
        except Exception as e:
            print(e)
    return render_template('bot.html', answer="")


@app.route("/translate", methods=["GET", "POST"])
def translate():
    global buddy
    buddy = None
    try:
        if request.method == "GET":
            return render_template('translator.html', answer_translate="Ну, давай! Введи текст!",
                                   time="Нет время.")
        elif request.method == "POST":
            try:
                ask = request.form['ask']
                lang1 = request.form['lang']
                lang2 = request.form['lang1']
                lang = f"{lang1}-{lang2}"
                if ask:
                    answer = bot_message.translate_bot(ask, lang)
                    t = str(datetime.today()).split()
                    time = t[1][:-10] + ' ' + '.'.join(t[0].split('-')[::-1])
                    return render_template('translator.html', answer_translate=answer, time=time)
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)
    return render_template('translator.html', answer_translate="Ну, давай! Введи текст!",
                           time="Нет время.")


@app.route("/dialog_go", methods=["GET", "POST"])
def dialog_go():
    global dialog, buddy
    name = player.email
    if dialog is None:
        with open('dialogs.pickle', 'rb') as f:
            dialog = pickle.load(f)
            print(dialog)
    if request.method == "GET":
        session = db_session.create_session()
        users = [user.email for user in session.query(User) if user.email != name]
        session.commit()
        if buddy is None:
            if name not in dialog:
                if len(users) != 0:
                    buddy = random.choice(users)
                    dialog[name] = {'friends': [buddy]}
                    dialog[name][buddy] = []
                    dialog[buddy] = {'friends': [name]}
                    dialog[buddy][name] = []
                    return render_template('dialog.html', have=True, go=False,
                                           friend=str(buddy.split('@')[0].capitalize()))
                return render_template('dialog.html', have=False)
            else:
                if len(users) != 0:
                    have_dialog = dialog[name]['friends']
                    for x in have_dialog:
                        i = users.index(x)
                        del users[i]
                    if len(users) == 0:
                        return render_template('dialog.html', have=False)
                    else:
                        buddy = random.choice(users)
                        dialog[name]['friends'].append(buddy)
                        dialog[name][buddy] = []
                        if buddy in dialog:
                            dialog[buddy]['friends'].append(name)
                            dialog[buddy][name] = []
                        else:
                            dialog[buddy] = {'friends': [name]}
                            dialog[buddy][name] = []
                        return render_template('dialog.html', have=True, go=False,
                                               friend=str(buddy.split('@')[0].capitalize()))
        return render_template('dialog.html', have=True, go=True, dialog=dialog[name][buddy],
                               friend=str(buddy.split('@')[0].capitalize()))
    elif request.method == "POST":
        ask = request.form['ask']
        t = str(datetime.today()).split()
        time = t[1][:-10] + ' ' + '.'.join(t[0].split('-')[::-1])
        dialog[name][buddy].append((str(name.split('@')[0].capitalize()), ask, time))
        dialog[buddy][name].append((str(name.split('@')[0].capitalize()), ask, time))
        return render_template('dialog.html', have=True, go=True, name=str(name.split('@')[0].capitalize()),
                               dialog=dialog[name][buddy], friend=str(buddy.split('@')[0].capitalize()))


@app.route("/have_dialog", methods=["GET", "POST"])
def have_dialog():
    global dialog, buddy
    buddy = None
    name = player.email
    if dialog is None:
        with open('dialogs.pickle', 'rb') as f:
            dialog = pickle.load(f)
    session = db_session.create_session()
    users = [user for user in session.query(User) if user.email != name]
    session.commit()
    friends = dialog[name]['friends']
    fr = []
    for f in friends:
        for u in users:
            if f == u.email:
                fr.append((f.split('@')[0].capitalize(), u.img, f))
    return render_template('have_dialog.html', friends=fr, name=str(name.split('@')[0].capitalize()))


@app.route("/now_dialog", methods=["GET", "POST"])
def now_dialog():
    global dialog, buddy
    buddy = request.form['name']
    name = player.email
    if dialog is None:
        with open('dialogs.pickle', 'rb') as f:
            dialog = pickle.load(f)
    return render_template('dialog.html', have=True, go=True, name=str(name.split('@')[0].capitalize()),
                           dialog=dialog[name][buddy], friend=str(buddy.split('@')[0].capitalize()))


@app.route("/music_instrumental", methods=["GET", "POST"])
def music_instrumental():
    music = get_music(GENRE[0])
    return render_template('music.html', music=music)


@app.route("/music_classical", methods=["GET", "POST"])
def music_classical():
    music = get_music(GENRE[1])
    return render_template('music.html', music=music)


@app.route("/music_electronic", methods=["GET", "POST"])
def music_electronic():
    music = get_music(GENRE[2])
    return render_template('music.html', music=music)


@app.route("/music_latin", methods=["GET", "POST"])
def music_latin():
    music = get_music(GENRE[3])
    return render_template('music.html', music=music)


@app.route("/music_hip_hop", methods=["GET", "POST"])
def music_hip_hop():
    music = get_music(GENRE[4])
    return render_template('music.html', music=music)


@app.route("/music_country", methods=["GET", "POST"])
def music_country():
    music = get_music(GENRE[5])
    return render_template('music.html', music=music)


@app.route("/music_metal", methods=["GET", "POST"])
def music_metal():
    music = get_music(GENRE[6])
    return render_template('music.html', music=music)


@app.route("/music_reggae", methods=["GET", "POST"])
def music_reggae():
    music = get_music(GENRE[7])
    return render_template('music.html', music=music)


@app.route("/music_blues", methods=["GET", "POST"])
def music_blues():
    music = get_music(GENRE[8])
    return render_template('music.html', music=music)


@app.route("/music_folk", methods=["GET", "POST"])
def music_folk():
    music = get_music(GENRE[9])
    return render_template('music.html', music=music)


@app.route("/music_jazz", methods=["GET", "POST"])
def music_jazz():
    music = get_music(GENRE[10])
    return render_template('music.html', music=music)


@app.route("/music_pop", methods=["GET", "POST"])
def music_pop():
    music = get_music(GENRE[11])
    return render_template('music.html', music=music)


@app.route("/music_rock", methods=["GET", "POST"])
def music_rock():
    music = get_music(GENRE[12])
    return render_template('music.html', music=music)


@app.route("/music_ska", methods=["GET", "POST"])
def music_ska():
    music = get_music(GENRE[13])
    return render_template('music.html', music=music)


@app.route("/random_music", methods=["GET", "POST"])
def random_music():
    music = get_music(random.choice(GENRE))
    return render_template('music.html', music=music)


if __name__ == '__main__':
    db_session.global_init("db/users.sqlite")
    app.run(port=8080, host='127.0.0.1')
