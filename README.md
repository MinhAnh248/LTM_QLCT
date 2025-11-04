# 🏗️ Expense Manager - 3-Layer Architecture

## 🎯 **Tổng quan kiến trúc**

Hệ thống được thiết kế với 3 layer bảo mật:

### 🌐 **WAN Layer** - Dành cho Users thông thường (PUBLIC ACCESS)
- **URL**: `http://localhost` (port 80) hoặc `https://your-domain.com`
- **Truy cập**: Từ MỌI MẠNG (4G, Wifi nhà, công ty, quán cà phê...)
- **Chức năng**: Đăng ký, đăng nhập, quản lý chi tiêu CÁ NHÂN
- **Bảo mật**: Users chỉ thấy data của chính mình
- **Không cần**: VPN, cấu hình mạng đặc biệt

### 🏢 **LAN Layer** - Backend Internal
- **URL**: `http://localhost:5001` (chỉ internal)
- **Chức năng**: API xử lý business logic, database operations
- **Bảo mật**: Không exposed ra internet, chỉ WAN và VPN gọi được

### 🔐 **VPN Layer** - Dành cho Admin
- **URL**: `http://localhost:8501` (qua VPN)
- **Chức năng**: Xem TẤT CẢ data, quản lý users, system monitoring
- **Bảo mật**: Chỉ admin có VPN mới truy cập được

---

## 🚀 **Cách chạy hệ thống**

### **Bước 1: Khởi động tất cả services**
```bash
# Copy file cấu hình
cp .env.example .env

# Chạy tất cả containers
docker-compose up -d

# Kiểm tra status
docker-compose ps
```

### **Bước 2: Khởi tạo database**
```bash
# Gọi API khởi tạo database (cần admin secret)
curl -X POST http://localhost:5001/init_db \
  -H "Admin-Secret: admin-secret-key"
```

---

## 👥 **Hướng dẫn cho Users thông thường**

### **Truy cập ứng dụng từ BẤT KỲ MẠNG NÀO**
📱 **Từ điện thoại 4G**: Mở browser → `https://your-domain.com`
💻 **Từ Wifi nhà**: Mở laptop → `https://your-domain.com`
🏢 **Từ mạng công ty**: Mở máy tính → `https://your-domain.com`
☕ **Từ quán cà phê**: Mở điện thoại → `https://your-domain.com`

### **Các bước sử dụng**
1. Mở browser bất kỳ: `http://localhost` (local) hoặc `https://your-domain.com` (production)
2. Đăng ký tài khoản mới
3. Đăng nhập
4. Thêm chi tiêu cá nhân

### **⚠️ Không cần**
- ❌ VPN để truy cập WAN
- ❌ Cấu hình mạng đặc biệt
- ❌ Whitelist IP
- ❌ Cài đặt phần mềm thêm

### **Chức năng Users có thể làm**
- ✅ Đăng ký/Đăng nhập
- ✅ Thêm/sửa/xóa chi tiêu của mình
- ✅ Xem dashboard cá nhân
- ✅ Xem báo cáo chi tiêu của mình
- ❌ KHÔNG thể xem data của users khác
- ❌ KHÔNG thể truy cập admin panel

---

## 🔐 **Hướng dẫn cho Admin**

### **Truy cập Admin Panel**
1. **Kết nối VPN** (trong production)
2. Mở browser: `http://localhost:8501`
3. Đăng nhập admin:
   - Username: `admin`
   - Password: `admin123`

### **Chức năng Admin có thể làm**
- ✅ Xem TẤT CẢ users trong hệ thống
- ✅ Xem TẤT CẢ chi tiêu của TẤT CẢ users
- ✅ Ban/Unban users
- ✅ Xem system logs
- ✅ Monitor server performance
- ✅ Backup/restore database
- ✅ System analytics

---

## 🔒 **Bảo mật**

### **WAN Security**
- HTTPS bắt buộc (production)
- JWT authentication
- Rate limiting
- SQL injection protection
- Input validation

### **LAN Security**
- Không exposed ra internet
- Internal-Secret key required
- IP whitelist
- Database encryption

### **VPN Security**
- Admin authentication required
- Admin-Secret key required
- VPN connection required (production)
- Session timeout

---

## 🛠️ **Development**

### **Cấu trúc project**
```
LTM_QLCT/
├── WAN/                 # Public web app
│   ├── app.py
│   ├── templates/
│   └── Dockerfile
├── LAN/                 # Internal API
│   ├── app.py
│   ├── services/
│   └── Dockerfile
├── VPN/                 # Admin dashboard
│   ├── admin_dashboard.py
│   └── Dockerfile
└── docker-compose.yml
```

### **Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/expense_db

# Security
INTERNAL_SECRET=secret-key-for-wan-to-lan
ADMIN_SECRET=secret-key-for-admin-access

# APIs
LAN_API_URL=http://lan-app:5001
```

### **API Endpoints**

#### **WAN → LAN (Internal)**
- `POST /api/register_user` - Đăng ký user
- `POST /api/authenticate_user` - Xác thực login
- `GET /api/user_stats` - Thống kê user
- `GET /api/get_user_expenses` - Lấy chi tiêu user
- `POST /api/add_expense` - Thêm chi tiêu

#### **VPN → LAN (Admin)**
- `GET /admin/system_stats` - Thống kê hệ thống
- `GET /admin/all_users` - Tất cả users
- `GET /admin/all_expenses` - Tất cả chi tiêu
- `POST /admin/ban_user` - Ban user

---

## 🧪 **Testing**

### **Test User Flow**
```bash
# 1. Đăng ký user mới
curl -X POST http://localhost/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@email.com", "password": "123456"}'

# 2. Đăng nhập
curl -X POST http://localhost/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@email.com", "password": "123456"}'
```

### **Test Admin Flow**
```bash
# 1. Xem tất cả users (cần admin secret)
curl -X GET http://localhost:5001/admin/all_users \
  -H "Admin-Secret: admin-secret-key"

# 2. Xem tất cả expenses
curl -X GET http://localhost:5001/admin/all_expenses \
  -H "Admin-Secret: admin-secret-key"
```

---

## 📊 **Monitoring**

### **Health Checks**
```bash
# WAN health
curl http://localhost/

# LAN health (internal)
curl http://localhost:5001/admin/system_stats \
  -H "Admin-Secret: admin-secret-key"

# VPN health
curl http://localhost:8501/
```

### **Logs**
```bash
# Xem logs containers
docker-compose logs wan-app
docker-compose logs lan-app
docker-compose logs vpn-admin
```

---

## 🚨 **Troubleshooting**

### **Lỗi thường gặp**

1. **"Forbidden - Internal access only"**
   - Kiểm tra `INTERNAL_SECRET` trong .env
   - Đảm bảo WAN gửi đúng header

2. **"Admin access only"**
   - Kiểm tra `ADMIN_SECRET`
   - Đảm bảo VPN gửi đúng header

3. **Database connection error**
   - Kiểm tra PostgreSQL container
   - Verify `DATABASE_URL`

4. **Cannot access admin panel**
   - Kiểm tra VPN connection (production)
   - Verify admin credentials

---

## 📈 **Production Deployment**

### **Security Checklist**
- [ ] Setup proper VPN (WireGuard)
- [ ] Change all default passwords
- [ ] Enable HTTPS with SSL certificates
- [ ] Setup firewall rules
- [ ] Enable database encryption
- [ ] Setup backup strategy
- [ ] Configure monitoring alerts

### **Scaling**
- Load balancer cho WAN layer
- Multiple LAN instances
- Database replication
- Redis cluster
- CDN cho static files

---

## 👨💻 **Contact**

Nếu có vấn đề, liên hệ admin qua VPN dashboard hoặc system logs.

**Lưu ý**: Đây là hệ thống demo. Trong production cần thêm nhiều tính năng bảo mật khác.