# 🚀 Deploy WAN lên Render.com

## 🎯 **Tổng quan**
Deploy WAN layer lên Render để users có thể truy cập từ mọi mạng với URL công khai.

---

## 📋 **Bước 1: Chuẩn bị**

### **1.1 Tạo GitHub Repository**
```bash
# Tạo repo mới trên GitHub
# Push code lên GitHub
git init
git add .
git commit -m "Initial commit - Expense Manager"
git branch -M main
git remote add origin https://github.com/your-username/expense-manager.git
git push -u origin main
```

### **1.2 Cấu trúc project cho Render**
```
LTM_QLCT/
├── WAN/                    # Sẽ deploy lên Render
│   ├── app.py
│   ├── requirements.txt
│   ├── gunicorn.conf.py
│   └── templates/
├── render.yaml             # Cấu hình Render
└── RENDER_DEPLOY.md
```

---

## 🌐 **Bước 2: Deploy WAN lên Render**

### **2.1 Tạo Web Service**
1. Đăng nhập [render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repository
4. Cấu hình:

```yaml
Name: expense-manager-wan
Environment: Python 3
Region: Singapore (gần VN nhất)
Branch: main
Build Command: cd WAN && pip install -r requirements.txt
Start Command: cd WAN && gunicorn --config gunicorn.conf.py app:app
```

### **2.2 Environment Variables**
Thêm các biến môi trường:

```bash
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
INTERNAL_SECRET=internal-api-secret-key
LAN_API_URL=https://expense-manager-lan.onrender.com
DATABASE_URL=postgresql://user:pass@host:5432/db
```

### **2.3 Health Check**
```
Health Check Path: /health
```

---

## 🗄️ **Bước 3: Setup Database**

### **3.1 Tạo PostgreSQL Database**
1. Trong Render Dashboard → **"New +"** → **"PostgreSQL"**
2. Cấu hình:
```yaml
Name: expense-manager-db
Database Name: expense_manager
User: expense_user
Region: Singapore
Plan: Free
```

### **3.2 Lấy Database URL**
```bash
# Render sẽ tự tạo DATABASE_URL
# Copy và paste vào Environment Variables của WAN service
DATABASE_URL=postgresql://expense_user:password@host:5432/expense_manager
```

---

## 🔧 **Bước 4: Deploy LAN (Optional)**

### **4.1 Tạo Background Worker cho LAN**
```yaml
Name: expense-manager-lan
Environment: Python 3
Build Command: cd LAN && pip install -r requirements.txt
Start Command: cd LAN && python app.py
```

### **4.2 Environment Variables cho LAN**
```bash
FLASK_ENV=production
INTERNAL_SECRET=internal-api-secret-key
ADMIN_SECRET=admin-panel-secret-key
DATABASE_URL=postgresql://expense_user:password@host:5432/expense_manager
```

---

## 🚀 **Bước 5: Khởi tạo Database**

### **5.1 Sau khi deploy thành công**
```bash
# Gọi API khởi tạo database
curl -X POST https://expense-manager-lan.onrender.com/init_db \
  -H "Admin-Secret: admin-panel-secret-key"
```

### **5.2 Kiểm tra kết nối**
```bash
# Test WAN service
curl https://expense-manager-wan.onrender.com/health

# Test LAN service  
curl https://expense-manager-lan.onrender.com/admin/system_stats \
  -H "Admin-Secret: admin-panel-secret-key"
```

---

## 🌍 **Bước 6: Truy cập Public**

### **6.1 URL công khai**
```
WAN (Users): https://expense-manager-wan.onrender.com
LAN (Internal): https://expense-manager-lan.onrender.com
```

### **6.2 Test từ các mạng khác nhau**
```bash
# Từ điện thoại 4G
https://expense-manager-wan.onrender.com

# Từ WiFi nhà
https://expense-manager-wan.onrender.com

# Từ mạng công ty
https://expense-manager-wan.onrender.com
```

---

## 🔒 **Bước 7: Bảo mật Production**

### **7.1 Environment Variables bảo mật**
```bash
# Tạo secret keys mạnh
SECRET_KEY=$(openssl rand -hex 32)
INTERNAL_SECRET=$(openssl rand -hex 32)
ADMIN_SECRET=$(openssl rand -hex 32)
```

### **7.2 Rate Limiting**
```python
# Đã cấu hình trong WAN/app.py
# 200 requests/day, 50 requests/hour
# 5 login attempts/minute
```

### **7.3 HTTPS**
```bash
# Render tự động enable HTTPS
# Certificate tự động renew
# HTTP redirect to HTTPS
```

---

## 📊 **Bước 8: Monitoring**

### **8.1 Render Dashboard**
- CPU/Memory usage
- Request logs
- Error logs
- Uptime monitoring

### **8.2 Health Checks**
```bash
# Render tự động ping /health endpoint
# Restart service nếu unhealthy
```

---

## 💰 **Chi phí**

### **Free Tier Limits**
```
Web Service: 750 hours/month (đủ cho 1 app)
Database: 1GB storage, 1 million rows
Bandwidth: 100GB/month
Sleep after 15 minutes inactive
```

### **Paid Plans** (nếu cần)
```
Starter: $7/month - No sleep, custom domains
Pro: $25/month - More resources, priority support
```

---

## 🚨 **Troubleshooting**

### **Lỗi thường gặp**

1. **Build failed**
```bash
# Kiểm tra requirements.txt
# Đảm bảo Python version tương thích
```

2. **Database connection error**
```bash
# Kiểm tra DATABASE_URL
# Đảm bảo database đã được tạo
```

3. **Service không start**
```bash
# Kiểm tra Start Command
# Xem logs trong Render dashboard
```

4. **CORS errors**
```bash
# Đã cấu hình CORS trong app.py
# Allow all origins for public access
```

---

## ✅ **Kết quả**

Sau khi deploy thành công:

### **🌐 Users có thể truy cập từ:**
- 📱 Điện thoại 4G/5G: `https://expense-manager-wan.onrender.com`
- 💻 WiFi nhà: `https://expense-manager-wan.onrender.com`
- 🏢 Mạng công ty: `https://expense-manager-wan.onrender.com`
- ☕ WiFi quán cà phê: `https://expense-manager-wan.onrender.com`

### **🔧 Admin có thể:**
- Quản lý qua VPN local: `http://localhost:8501`
- Hoặc deploy VPN lên Render riêng biệt

### **📈 Performance:**
- Global CDN
- Auto-scaling
- 99.9% uptime
- SSL/HTTPS tự động

---

## 🎉 **Demo URLs**

```bash
# Đăng ký user mới
curl -X POST https://expense-manager-wan.onrender.com/register \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@email.com", "password": "123456"}'

# Đăng nhập
curl -X POST https://expense-manager-wan.onrender.com/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@email.com", "password": "123456"}'
```

**🎯 Mục tiêu đạt được: Users từ MỌI MẠNG có thể sử dụng ứng dụng!**