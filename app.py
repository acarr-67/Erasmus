# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Global variable that will be updated by ESP
x_value = 0

# User model for authentication
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', x_value=x_value)

@app.route('/api/x', methods=['GET'])
def get_x():
    return jsonify({'x': x_value})

@app.route('/api/x', methods=['POST'])
def update_x():
    global x_value
    data = request.get_json()
    if 'x' in data:
        try:
            x_value = float(data['x'])
            return jsonify({'success': True, 'x': x_value})
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid value for x'}), 400
    return jsonify({'success': False, 'message': 'No x value provided'}), 400

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password or not confirm_password:
            flash('Tüm alanları doldurun', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Şifreler eşleşmiyor', 'danger')
            return render_template('register.html')
            
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Bu kullanıcı adı zaten alınmış', 'danger')
            return render_template('register.html')
            
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Hesabınız başarıyla oluşturuldu', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Kullanıcı adı ve şifre gerekli', 'danger')
            return render_template('login.html')
            
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = username
            flash('Başarıyla giriş yapıldı', 'success')
            return redirect(url_for('home'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Başarıyla çıkış yapıldı', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
