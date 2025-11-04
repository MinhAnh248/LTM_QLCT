from flask import Flask, request, jsonify
from functools import wraps
import os
import hashlib
import uuid
from datetime import datetime
import json
import psycopg

app = Flask(__name__)

# Database connection
def get_db():
    conn = psycopg.connect(os.getenv('DATABASE_URL'))
    return conn

# Redis connection (disabled for local testing)
# redis_client = None

# Security decorators
def verify_internal_request(f):
    """Chỉ cho phép WAN gọi"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        secret = request.headers.get('Internal-Secret')
        if secret != os.getenv('INTERNAL_SECRET', 'secret-key'):
            return jsonify({"error": "Forbidden - Internal access only"}), 403
        return f(*args, **kwargs)
    return decorated_function

def verify_admin_request(f):
    """Chỉ cho phép VPN (Admin) gọi"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_secret = request.headers.get('Admin-Secret')
        if admin_secret != os.getenv('ADMIN_SECRET', 'admin-secret-key'):
            return jsonify({"error": "Admin access only"}), 403
        return f(*args, **kwargs)
    return decorated_function

# ===== USER MANAGEMENT APIs (cho WAN) =====
@app.route('/api/register_user', methods=['POST'])
@verify_internal_request
def register_user():
    """Đăng ký user mới"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email và password là bắt buộc'}), 400
    
    # Hash password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user_id = str(uuid.uuid4())
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Check existing user
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({'error': 'Email đã được sử dụng'}), 400
        
        # Insert new user
        cur.execute("""
            INSERT INTO users (id, email, password_hash, created_at, is_active)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, email, password_hash, datetime.now(), True))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Log event
        log_system_event('USER_REGISTERED', {'user_id': user_id, 'email': email})
        
        return jsonify({'success': True, 'user_id': user_id}), 201
        
    except Exception as e:
        return jsonify({'error': 'Lỗi database'}), 500

@app.route('/api/authenticate_user', methods=['POST'])
@verify_internal_request
def authenticate_user():
    """Xác thực user login"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, email, is_active FROM users 
            WHERE email = %s AND password_hash = %s
        """, (email, password_hash))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Email hoặc password không đúng'}), 401
        
        if not user['is_active']:
            return jsonify({'error': 'Tài khoản đã bị khóa'}), 401
        
        # Log login
        log_system_event('USER_LOGIN', {'user_id': user['id'], 'email': user['email']})
        
        return jsonify({
            'user_id': user['id'],
            'email': user['email']
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Lỗi database'}), 500

@app.route('/api/get_user', methods=['GET'])
@verify_internal_request
def get_user():
    """Lấy thông tin user"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT id, email FROM users WHERE id = %s AND is_active = true", (user_id,))
        user = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if user:
            return jsonify(dict(user)), 200
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'error': 'Lỗi database'}), 500

# ===== EXPENSE APIs (cho WAN) =====
@app.route('/api/user_stats', methods=['GET'])
@verify_internal_request
def user_stats():
    """Tính thống kê cho 1 user cụ thể"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Tổng chi tiêu tháng này
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) as total_this_month
            FROM expenses 
            WHERE user_id = %s 
            AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)
            AND EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
        """, (user_id,))
        total_this_month = cur.fetchone()['total_this_month']
        
        # Chi tiêu theo danh mục
        cur.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses 
            WHERE user_id = %s 
            AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)
            GROUP BY category
            ORDER BY total DESC
        """, (user_id,))
        by_category = cur.fetchall()
        
        # Số giao dịch
        cur.execute("SELECT COUNT(*) as count FROM expenses WHERE user_id = %s", (user_id,))
        total_transactions = cur.fetchone()['count']
        
        cur.close()
        conn.close()
        
        return jsonify({
            'total_this_month': float(total_this_month),
            'by_category': [dict(row) for row in by_category],
            'total_transactions': total_transactions
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Lỗi database'}), 500

@app.route('/api/get_user_expenses', methods=['GET'])
@verify_internal_request
def get_user_expenses():
    """Lấy chi tiêu CỦA 1 USER (không phải tất cả)"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, amount, category, description, created_at
            FROM expenses 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 100
        """, (user_id,))
        
        expenses = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([dict(row) for row in expenses]), 200
        
    except Exception as e:
        return jsonify({'error': 'Lỗi database'}), 500

@app.route('/api/add_expense', methods=['POST'])
@verify_internal_request
def add_expense():
    """Thêm chi tiêu mới"""
    data = request.get_json()
    user_id = data.get('user_id')
    amount = data.get('amount')
    category = data.get('category')
    description = data.get('description', '')
    
    if not user_id or not amount or not category:
        return jsonify({'error': 'user_id, amount, category là bắt buộc'}), 400
    
    expense_id = str(uuid.uuid4())
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO expenses (id, user_id, amount, category, description, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (expense_id, user_id, amount, category, description, datetime.now()))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Queue background job để check budget (disabled for local)
        # from workers.budget_checker import check_user_budget
        # check_user_budget.delay(user_id)
        
        # Log event
        log_system_event('EXPENSE_ADDED', {
            'user_id': user_id, 
            'expense_id': expense_id, 
            'amount': amount,
            'category': category
        })
        
        return jsonify({
            'success': True, 
            'expense_id': expense_id,
            'message': 'Thêm chi tiêu thành công'
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Lỗi database'}), 500

# ===== ADMIN APIs (chỉ cho VPN) =====
@app.route('/admin/system_stats', methods=['GET'])
@verify_admin_request
def admin_system_stats():
    """Thống kê toàn hệ thống - CHỈ ADMIN"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Tổng users
        cur.execute("SELECT COUNT(*) as total FROM users")
        total_users = cur.fetchone()['total']
        
        # Tổng expenses
        cur.execute("SELECT COUNT(*) as total FROM expenses")
        total_expenses = cur.fetchone()['total']
        
        # Tổng amount
        cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM expenses")
        total_amount = cur.fetchone()['total']
        
        # Active users (login trong 24h)
        cur.execute("""
            SELECT COUNT(DISTINCT user_id) as active 
            FROM system_logs 
            WHERE event_type = 'USER_LOGIN' 
            AND created_at > NOW() - INTERVAL '24 hours'
        """)
        active_users = cur.fetchone()['active']
        
        cur.close()
        conn.close()
        
        return jsonify({
            'total_users': total_users,
            'total_expenses': total_expenses,
            'total_amount': float(total_amount),
            'active_users': active_users
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Lỗi database'}), 500

@app.route('/admin/all_users', methods=['GET'])
@verify_admin_request
def admin_all_users():
    """Lấy TẤT CẢ users - CHỈ ADMIN"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, email, created_at, is_active,
                   (SELECT COUNT(*) FROM expenses WHERE user_id = users.id) as expense_count,
                   (SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = users.id) as total_spent
            FROM users 
            ORDER BY created_at DESC
        """)
        
        users = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([dict(row) for row in users]), 200
        
    except Exception as e:
        return jsonify({'error': 'Lỗi database'}), 500

@app.route('/admin/all_expenses', methods=['GET'])
@verify_admin_request
def admin_all_expenses():
    """Lấy TẤT CẢ expenses - CHỈ ADMIN"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT e.id, e.amount, e.category, e.description, e.created_at,
                   u.email as user_email
            FROM expenses e
            JOIN users u ON e.user_id = u.id
            ORDER BY e.created_at DESC
            LIMIT 1000
        """)
        
        expenses = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([dict(row) for row in expenses]), 200
        
    except Exception as e:
        return jsonify({'error': 'Lỗi database'}), 500

@app.route('/admin/ban_user', methods=['POST'])
@verify_admin_request
def admin_ban_user():
    """Ban user - CHỈ ADMIN"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("UPDATE users SET is_active = false WHERE id = %s", (user_id,))
        conn.commit()
        
        cur.close()
        conn.close()
        
        # Log admin action
        log_system_event('USER_BANNED', {'user_id': user_id, 'admin_action': True})
        
        return jsonify({'success': True, 'message': 'User đã bị ban'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Lỗi database'}), 500

# ===== UTILITY FUNCTIONS =====
def log_system_event(event_type, data):
    """Log system events"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO system_logs (id, event_type, data, created_at)
            VALUES (%s, %s, %s, %s)
        """, (str(uuid.uuid4()), event_type, json.dumps(data), datetime.now()))
        
        conn.commit()
        cur.close()
        conn.close()
    except:
        pass  # Không crash app nếu log fail

# Health check endpoint for Render
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'LAN'}), 200

# ===== DATABASE INITIALIZATION =====
@app.route('/init_db', methods=['POST'])
@verify_admin_request
def init_database():
    """Khởi tạo database - CHỈ ADMIN"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Create tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT true
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) REFERENCES users(id),
                amount DECIMAL(12,2) NOT NULL,
                category VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id VARCHAR(36) PRIMARY KEY,
                event_type VARCHAR(50) NOT NULL,
                data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Database initialized'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check endpoint
@app.route('/')
def health():
    return jsonify({
        'service': 'LAN Internal API',
        'status': 'running',
        'endpoints': {
            'admin': '/admin/system_stats',
            'init': '/init_db',
            'api': '/api/register_user'
        }
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)