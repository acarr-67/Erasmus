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
# app.py dosyasına eklenecek kodlar (mevcut kodu değiştirmeyin, aşağıdaki kodları sonuna ekleyin)

# Sensör değerleri için model
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    soil_moisture = db.Column(db.Integer, nullable=False)
    temp_status = db.Column(db.String(20), nullable=False)
    soil_status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SensorData {self.id}: Temp: {self.temperature}°C, Soil: {self.soil_moisture}>'

# Veritabanını güncelle
with app.app_context():
    db.create_all()

# Sensör verilerini al
@app.route('/api/sensor_data', methods=['POST'])
def receive_sensor_data():
    data = request.get_json()
    
    if not all(key in data for key in ['temperature', 'humidity', 'soil_moisture', 'temp_status', 'soil_status']):
        return jsonify({"success": False, "error": "Eksik veri"}), 400
    
    try:
        # Yeni sensör verisi oluştur
        new_data = SensorData(
            temperature=float(data['temperature']),
            humidity=float(data['humidity']),
            soil_moisture=int(data['soil_moisture']),
            temp_status=data['temp_status'],
            soil_status=data['soil_status']
        )
        
        # Veritabanına kaydet
        db.session.add(new_data)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Veriler başarıyla kaydedildi"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Son sensör verilerini görüntüle
@app.route('/sensor_dashboard')
@login_required
def sensor_dashboard():
    # En son eklenen veriyi al
    latest_data = SensorData.query.order_by(SensorData.timestamp.desc()).first()
    
    # Son 24 saate ait sıcaklık verileri
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    temp_data = SensorData.query.filter(SensorData.timestamp >= one_day_ago).all()
    
    # Grafik için veri hazırla
    timestamps = [data.timestamp.strftime('%H:%M') for data in temp_data]
    temperatures = [data.temperature for data in temp_data]
    humidity_values = [data.humidity for data in temp_data]
    soil_values = [data.soil_moisture for data in temp_data]
    
    return render_template(
        'sensor_dashboard.html', 
        latest_data=latest_data,
        timestamps=timestamps,
        temperatures=temperatures,
        humidity_values=humidity_values,
        soil_values=soil_values
    )

# API ile en son sensör verilerini al 
@app.route('/api/latest_sensor_data', methods=['GET'])
def get_latest_sensor_data():
    latest_data = SensorData.query.order_by(SensorData.timestamp.desc()).first()
    
    if not latest_data:
        return jsonify({"success": False, "error": "Henüz sensör verisi yok"}), 404
    
    return jsonify({
        "success": True,
        "data": {
            "temperature": latest_data.temperature,
            "humidity": latest_data.humidity,
            "soil_moisture": latest_data.soil_moisture,
            "temp_status": latest_data.temp_status,
            "soil_status": latest_data.soil_status,
            "timestamp": latest_data.timestamp.strftime('%d.%m.%Y %H:%M:%S')
        }
    })
