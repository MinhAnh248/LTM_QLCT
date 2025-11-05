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
    conn.row_factory = psycopg.rows.dict_row
    return conn

# Redis connection (disabled for local testing)
# redis_client = None

# Security decorators
def verify_internal_request(f):
    """Chỉ cho phép từ cùng mạng LAN"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Kiểm tra IP client
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # Cho phép localhost và private IP ranges
        allowed_ips = [
            '127.0.0.1',
            'localhost',
        ]
        
        # Private IP ranges (LAN)
        if (client_ip.startswith('192.168.') or 
            client_ip.startswith('10.') or 
            client_ip.startswith('172.16.') or
            client_ip.startswith('172.31.') or
            client_ip in allowed_ips):
            return f(*args, **kwargs)
        
        # Kiểm tra secret key (cho WAN service)
        secret = request.headers.get('Internal-Secret')
        if secret == os.getenv('INTERNAL_SECRET', 'secret-key'):
            return f(*args, **kwargs)
        
        return jsonify({"error": "Forbidden - LAN access only"}), 403
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
            INSERT INTO users (id, email, password_hash, created_at, is_active, is_premium)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, email, password_hash, datetime.now(), True, False))
        
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
            SELECT u.id, u.email, u.is_active, u.is_premium,
                   COUNT(e.id) as expense_count
            FROM users u
            LEFT JOIN expenses e ON u.id = e.user_id
            WHERE u.email = %s AND u.password_hash = %s
            GROUP BY u.id, u.email, u.is_active, u.is_premium
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
            'email': user['email'],
            'expense_count': user.get('expense_count', 0),
            'is_premium': user.get('is_premium', False)
        }), 200
        
    except Exception as e:
        print(f"Authenticate error: {str(e)}")
        return jsonify({'error': f'Lỗi: {str(e)}'}), 500

@app.route('/api/get_user', methods=['GET'])
@verify_internal_request
def get_user():
    """Lấy thông tin user"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT u.id, u.email, u.is_premium, 
                   COUNT(e.id) as expense_count
            FROM users u
            LEFT JOIN expenses e ON u.id = e.user_id
            WHERE u.id = %s AND u.is_active = true
            GROUP BY u.id, u.email, u.is_premium
        """, (user_id,))
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
        try:
            cur.execute("""
                SELECT COUNT(DISTINCT user_id) as active 
                FROM system_logs 
                WHERE event_type = 'USER_LOGIN' 
                AND created_at > NOW() - INTERVAL '24 hours'
            """)
            result = cur.fetchone()
            active_users = result['active'] if result else 0
        except:
            active_users = 0
        
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

# ===== WEBHOOK để nhận data từ WAN =====
@app.route('/webhook/sync_data', methods=['POST'])
def webhook_sync_data():
    """Nhận dữ liệu từ WAN (không cần auth vì WAN push)"""
    data = request.get_json()
    event_type = data.get('event_type')
    payload = data.get('data')
    
    try:
        if event_type == 'USER_REGISTERED':
            # Lưu user vào LAN database
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (id, email, password_hash, created_at, is_active, is_premium)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (payload['user_id'], payload['email'], payload['password_hash'], 
                   datetime.now(), True, False))
            conn.commit()
            cur.close()
            conn.close()
            
        elif event_type == 'EXPENSE_ADDED':
            # Lưu expense vào LAN database
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO expenses (id, user_id, amount, category, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (payload['expense_id'], payload['user_id'], payload['amount'],
                   payload['category'], payload['description'], datetime.now()))
            conn.commit()
            cur.close()
            conn.close()
        
        log_system_event(event_type, payload)
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
@app.route('/init_db', methods=['POST', 'GET'])
def init_database():
    """Khởi tạo database"""
    if request.method == 'GET':
        return '''
        <html>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>Init Database</h1>
            <form method="POST">
                <button type="submit" style="padding: 15px 30px; font-size: 18px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer;">Initialize Database</button>
            </form>
        </body>
        </html>
        '''
    
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
                is_active BOOLEAN DEFAULT true,
                is_premium BOOLEAN DEFAULT false
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

# Admin Dashboard Web Interface
@app.route('/admin')
def admin_dashboard():
    return '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - LAN</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; text-align: center; margin-bottom: 30px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #3498db; }
        .stat-label { color: #666; margin-top: 5px; }
        .section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .section h2 { margin-bottom: 15px; color: #2c3e50; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: bold; }
        .btn { background: #e74c3c; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #c0392b; }
        .auth-form { max-width: 400px; margin: 100px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .login-btn { width: 100%; background: #3498db; color: white; padding: 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .login-btn:hover { background: #2980b9; }
        .error { color: #e74c3c; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="auth-form">
        <h2 style="text-align: center; margin-bottom: 30px;">🔒 Admin Dashboard</h2>
        <div class="form-group">
            <label>Admin Secret:</label>
            <input type="password" id="adminSecret" placeholder="Nhập Admin Secret">
        </div>
        <button onclick="loadDashboard()" class="login-btn">Truy cập Dashboard</button>
        <div id="error" class="error"></div>
    </div>

    <div id="dashboard" style="display: none;">
        <div class="header">
            <h1>🔒 LAN Admin Dashboard</h1>
            <p>Quản lý hệ thống - Chỉ dành cho Admin</p>
        </div>

        <div class="container">
            <div class="stats" id="stats"></div>
            <div class="section">
                <h2>👥 Danh sách Users</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Email</th>
                            <th>Ngày tạo</th>
                            <th>Số giao dịch</th>
                            <th>Tổng chi tiêu</th>
                            <th>Trạng thái</th>
                            <th>Hành động</th>
                        </tr>
                    </thead>
                    <tbody id="usersTable"></tbody>
                </table>
            </div>

            <div class="section">
                <h2>💰 Giao dịch gần đây</h2>
                <table>
                    <thead>
                        <tr>
                            <th>User</th>
                            <th>Số tiền</th>
                            <th>Danh mục</th>
                            <th>Mô tả</th>
                            <th>Ngày</th>
                        </tr>
                    </thead>
                    <tbody id="expensesTable"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        let adminSecret = "";

        async function loadDashboard() {
            adminSecret = document.getElementById("adminSecret").value;
            if (!adminSecret) {
                document.getElementById("error").textContent = "Vui lòng nhập Admin Secret";
                return;
            }

            try {
                const statsResponse = await fetch("/admin/system_stats", {
                    headers: { "Admin-Secret": adminSecret }
                });
                
                if (!statsResponse.ok) {
                    document.getElementById("error").textContent = "Admin Secret không đúng";
                    return;
                }

                const stats = await statsResponse.json();
                
                const usersResponse = await fetch("/admin/all_users", {
                    headers: { "Admin-Secret": adminSecret }
                });
                const users = await usersResponse.json();

                const expensesResponse = await fetch("/admin/all_expenses", {
                    headers: { "Admin-Secret": adminSecret }
                });
                const expenses = await expensesResponse.json();

                document.querySelector(".auth-form").style.display = "none";
                document.getElementById("dashboard").style.display = "block";

                document.getElementById("stats").innerHTML = `
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_users}</div>
                        <div class="stat-label">Tổng Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_expenses}</div>
                        <div class="stat-label">Tổng Giao dịch</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">$${stats.total_amount.toFixed(2)}</div>
                        <div class="stat-label">Tổng Chi tiêu</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.active_users}</div>
                        <div class="stat-label">Users Hoạt động (24h)</div>
                    </div>
                `;

                document.getElementById("usersTable").innerHTML = users.map(user => `
                    <tr>
                        <td>${user.email}</td>
                        <td>${new Date(user.created_at).toLocaleDateString("vi-VN")}</td>
                        <td>${user.expense_count}</td>
                        <td>$${user.total_spent.toFixed(2)}</td>
                        <td>${user.is_active ? "Hoạt động" : "Bị khóa"}</td>
                        <td>
                            ${user.is_active ? `<button class="btn" onclick="banUser(\"${user.id}\")">Ban</button>` : ""}
                        </td>
                    </tr>
                `).join("");

                document.getElementById("expensesTable").innerHTML = expenses.slice(0, 20).map(expense => `
                    <tr>
                        <td>${expense.user_email}</td>
                        <td>$${expense.amount.toFixed(2)}</td>
                        <td>${expense.category}</td>
                        <td>${expense.description || "N/A"}</td>
                        <td>${new Date(expense.created_at).toLocaleDateString("vi-VN")}</td>
                    </tr>
                `).join("");

            } catch (error) {
                document.getElementById("error").textContent = "Lỗi kết nối";
            }
        }

        async function banUser(userId) {
            if (!confirm("Bạn có chắc muốn ban user này?")) return;
            
            try {
                const response = await fetch("/admin/ban_user", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Admin-Secret": adminSecret
                    },
                    body: JSON.stringify({ user_id: userId })
                });
                
                if (response.ok) {
                    alert("User đã bị ban");
                    loadDashboard();
                } else {
                    alert("Lỗi khi ban user");
                }
            } catch (error) {
                alert("Lỗi kết nối");
            }
        }
    </script>
</body>
</html>
    '''

# Health check endpoint
@app.route('/')
def health():
    return jsonify({
        'service': 'LAN Internal API',
        'status': 'running',
        'endpoints': {
            'admin': '/admin',
            'admin_api': '/admin/system_stats',
            'init': '/init_db',
            'api': '/api/register_user'
        }
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)