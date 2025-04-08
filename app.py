from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # oturum yönetimi için gerekli

# Başlangıçta x değeri
x = 0

# Basit kullanıcı bilgileri
USERNAME = "admin"
PASSWORD = "1234"

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Hatalı giriş.")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    global x
    return render_template('dashboard.html', x_value=x)

# ESP için x değerini değiştirme
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

# ESP için x değerini alma
@app.route('/get_x', methods=['GET'])
def get_x():
    global x
    return {"x": x}, 200

if __name__ == '__main__':
    app.run(debug=True)
