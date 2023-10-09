from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Credenziali dell'app Twitch
client_id = 'YOUR_CLIENT_ID'
client_secret = 'YOUR_CLIENT_SECRET'
redirect_uri = 'http://localhost:5000/callback'

# Lista di credenziali utente da leggere da credentials.txt
user_credentials = []
with open('credentials.txt', 'r') as file:
    for line in file:
        username, password = line.strip().split(':')
        user_credentials.append((username, generate_password_hash(password)))

current_user_index = 0  # Indice per tenere traccia dell'account attualmente utilizzato

@app.route('/')
def home():
    if 'username' in session:
        return f'Benvenuto, {session["username"]}! <a href="/logout">Esci</a> <a href="/switch_user">Cambia Utente</a>'
    return 'Benvenuto al sito!'

@app.route('/login')
def login():
    global current_user_index
    if current_user_index < len(user_credentials):
        username, hashed_password = user_credentials[current_user_index]
        current_user_index += 1

        if 'username' not in session:
            session['username'] = username
            return redirect(url_for('twitch_login'))

    return 'Tutti gli account sono stati utilizzati.'

@app.route('/twitch_login')
def twitch_login():
    authorization_url = f'https://id.twitch.tv/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=user:edit:follows'
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')

    token_url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }

    response = requests.post(token_url, data=params)
    data = response.json()
    session['access_token'] = data['access_token']
    session['user_id'] = data['user_id']

    return redirect(url_for('follow_channel'))

@app.route('/follow_channel')
def follow_channel():
    if 'access_token' in session:
        access_token = session['access_token']
        user_id = session['user_id']
        channel_to_follow = 'canale_da_seguire'  # Inserisci il nome del canale da seguire
        follow_url = f'https://api.twitch.tv/helix/users/follows?from_id={user_id}&to_name={channel_to_follow}'

        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.post(follow_url, headers=headers)

        if response.status_code == 200:
            return f'Hai effettuato il login con successo e seguito il canale {channel_to_follow}! <a href="/">Torna alla homepage</a>'
        else:
            return 'Login riuscito, ma non è stato possibile seguire il canale.'

    return 'Errore: Accesso non autorizzato.'

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('access_token', None)
    session.pop('user_id', None)
    return 'Hai effettuato il logout con successo! <a href="/">Torna alla homepage</a>'

if __name__ == '__main__':
    app.run(debug=True)
