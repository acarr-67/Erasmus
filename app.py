from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime
import config

app = Flask(__name__)
app.config.from_object(config.Config)
db = SQLAlchemy(app)

# Global değişken
x_value = 0

# Kullanıcı modeli
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

# X değeri günlüğü
class XValueLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    updated_by = db.Column(db.String(80), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<XValueLog {self.id}: {self.value}>'

# Veritabanını oluştur
with app.app_context():
    db.create_all()

# Giriş gerektiren sayfalar için decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfayı görüntülemek için giriş yapmalısınız', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Ana sayfa
@app.route('/')
def index():
    return render_template('index.html')

# Kayıt sayfası
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Şifreler eşleşmiyor!', 'danger')
            return render_template('register.html')
        
        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()
        
        if user_exists:
            flash('Bu kullanıcı adı zaten kullanılıyor!', 'danger')
            return render_template('register.html')
        
        if email_exists:
            flash('Bu e-posta adresi zaten kullanılıyor!', 'danger')
            return render_template('register.html')
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Giriş sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Kullanıcı adı veya şifre yanlış!', 'danger')
            return render_template('login.html')
        
        session['user_id'] = user.id
        session['username'] = user.username
        
        flash('Giriş başarılı!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

# Çıkış
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Çıkış yapıldı', 'info')
    return redirect(url_for('index'))

# Kontrol paneli
@app.route('/dashboard')
@login_required
def dashboard():
    global x_value
    logs = XValueLog.query.order_by(XValueLog.updated_at.desc()).limit(10).all()
    return render_template('dashboard.html', x_value=x_value, logs=logs)

# X değerini al (ESP veya diğer cihazlar için API)
@app.route('/api/x', methods=['GET'])
def get_x():
    global x_value
    return jsonify({"value": x_value})

# X değerini güncelle (ESP veya diğer cihazlar için API)
@app.route('/api/x', methods=['POST'])
def update_x():
    global x_value
    data = request.get_json()
    
    if 'value' in data:
        try:
            x_value = int(data['value'])
            
            # Log kaydı tut
            new_log = XValueLog(
                value=x_value,
                updated_by="API" if 'username' not in session else session['username']
            )
            db.session.add(new_log)
            db.session.commit()
            
            return jsonify({"success": True, "value": x_value})
        except ValueError:
            return jsonify({"success": False, "error": "Geçersiz değer"}), 400
    else:
        return jsonify({"success": False, "error": "Değer sağlanmadı"}), 400

# X değerini web uygulaması üzerinden güncelle
@app.route('/update_x', methods=['POST'])
@login_required
def update_x_web():
    global x_value
    
    try:
        x_value = int(request.form.get('x_value'))
        
        # Log kaydı tut
        new_log = XValueLog(
            value=x_value,
            updated_by=session['username']
        )
        db.session.add(new_log)
        db.session.commit()
        
        flash('X değeri başarıyla güncellendi!', 'success')
    except ValueError:
        flash('Geçersiz değer!', 'danger')
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
