from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import datetime
import os
import json

app = Flask(__name__)
CORS(app)

# Конфигурация базы данных
DATABASE = 'leads.db'

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            debt_amount REAL,
            debt_type TEXT,
            quiz_answers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'new',
            notes TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Получение соединения с базой данных"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET'])
def health_check():
    """Проверка работоспособности API"""
    return jsonify({
        'status': 'success',
        'message': 'DropThatDebt API is running',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/leads', methods=['POST'])
def create_lead():
    """Создание нового лида"""
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('email'):
            return jsonify({
                'status': 'error',
                'message': 'Name and email are required'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO leads (name, email, phone, debt_amount, debt_type, quiz_answers)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data['email'],
            data.get('phone', ''),
            data.get('debt_amount', 0),
            data.get('debt_type', ''),
            json.dumps(data.get('quiz_answers', {}))
        ))
        
        lead_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Lead created successfully',
            'lead_id': lead_id
        }), 201
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error creating lead: {str(e)}'
        }), 500

@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Получение списка всех лидов"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, phone, debt_amount, debt_type, 
                   quiz_answers, created_at, status, notes
            FROM leads 
            ORDER BY created_at DESC
        ''')
        
        leads = []
        for row in cursor.fetchall():
            lead = {
                'id': row['id'],
                'name': row['name'],
                'email': row['email'],
                'phone': row['phone'],
                'debt_amount': row['debt_amount'],
                'debt_type': row['debt_type'],
                'quiz_answers': json.loads(row['quiz_answers']) if row['quiz_answers'] else {},
                'created_at': row['created_at'],
                'status': row['status'],
                'notes': row['notes']
            }
            leads.append(lead)
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'leads': leads,
            'total': len(leads)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching leads: {str(e)}'
        }), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
