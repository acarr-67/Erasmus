from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

x = 0
USERS_FILE = 'users.json'

# Kullanıcı dosyası varsa yükle, yoksa oluştur
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        if username in users and users[username] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Hatalı giriş.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        if username in users:
            return render_template('register.html', error="Bu kullanıcı adı zaten var.")
        users[username] = password
        save_users(users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    global x
    return render_template('dashboard.html', x_value=x, user=session.get('username'))

@app.route('/set_x', methods=['POST'])
def set_x():
    global x
    new_x = request.form.get('x')
    if new_x is not None:
        try:
            x = int(new_x)
            return f"x değişkeni güncellendi: {x}", 200
        except ValueError:
            return "Geçersiz değer", 400
    return "x değeri gerekli", 400

@app.route('/get_x', methods=['GET'])
def get_x():
    global x
    return {"x": x}, 200

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
