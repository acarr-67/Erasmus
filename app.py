from flask import Flask, request, jsonify, render_template
import json
import os

app = Flask(__name__)
DATA_FILE = 'data.json'

def read_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def write_data(new_entry):
    data = read_data()
    data.append(new_entry)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/', methods=['GET'])
def index():
    data = read_data()
    return render_template('index.html', data=data)

@app.route('/api/data', methods=['POST'])
def receive_data():
    content = request.get_json()
    if not content:
        return jsonify({'error': 'Invalid JSON'}), 400

    write_data(content)
    return jsonify({'status': 'success', 'data': content}), 200

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(read_data())

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
