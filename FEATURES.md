# 🎯 Tính năng của hệ thống

## 📋 Tổng quan

Hệ thống Expense Manager có **2 tính năng chính** từ nhánh minhtri và haidang:

### 1️⃣ **Bank Monitoring System** (từ nhánh minhtri)
Mô phỏng tấn công phishing và keylogging trên trang ngân hàng giả

### 2️⃣ **Premium Upgrade System** (từ nhánh haidang)  
Giới hạn 5 lần thêm chi tiêu miễn phí, yêu cầu nâng cấp để tiếp tục

---

## 🏦 Tính năng 1: Bank Monitoring System

### **Mô tả**
Đây là demo về tấn công phishing - người dùng truy cập trang ngân hàng giả, nhập thông tin đăng nhập, và admin có thể theo dõi real-time:
- 📸 Screen captures (chụp màn hình)
- ⌨️ Keylogging (ghi lại phím bấm)
- 🔐 Login credentials (tài khoản/mật khẩu)
- 💸 Transfer data (thông tin chuyển khoản)

### **Cách sử dụng**

#### **Người dùng (Victim)**
1. Truy cập: `https://expense-manager-wan.onrender.com/bank`
2. Chọn ngân hàng từ dropdown (VCB, TCB, ACB, MB, VPBank, Sacombank, BIDV, VIB)
3. Nhập thông tin:
   - Số tài khoản
   - Mật khẩu
   - Mã OTP
4. Click "Đăng nhập"
5. Thực hiện chuyển khoản (demo)

#### **Admin (Attacker)**
1. Truy cập: `https://expense-manager-wan.onrender.com/monitor`
2. Xem real-time:
   - **Login Attempts**: Tài khoản/mật khẩu/OTP bị đánh cắp
   - **Keylog Data**: Các phím người dùng bấm
   - **Screen Captures**: Ảnh chụp màn hình tự động mỗi 3 giây
   - **Transfer Data**: Thông tin chuyển khoản

### **Công nghệ**
- **Socket.IO**: Real-time communication
- **html2canvas**: Chụp màn hình
- **JavaScript Keylogger**: Ghi lại phím bấm
- **Flask-SocketIO**: Backend xử lý events

### **Demo Flow**
```
User truy cập /bank
    ↓
Nhập thông tin ngân hàng
    ↓
Socket.IO gửi data đến server
    ↓
Server broadcast đến admin room
    ↓
Admin xem real-time tại /monitor
```

---

## 💎 Tính năng 2: Premium Upgrade System

### **Mô tả**
Giới hạn người dùng miễn phí chỉ được thêm **5 chi tiêu**. Sau đó phải nâng cấp lên gói **Premium** để tiếp tục sử dụng.

### **Cách hoạt động**

#### **User Flow**
1. Đăng ký tài khoản mới → `expense_count = 0`, `is_premium = False`
2. Thêm chi tiêu lần 1-5 → Thành công ✅
3. Thêm chi tiêu lần 6 → ❌ Lỗi: "Bạn đã hết lượt sử dụng miễn phí"
4. Click "Nâng cấp" → Chuyển đến `/upgrade`
5. Thanh toán (demo) → `is_premium = True`
6. Thêm chi tiêu không giới hạn ✅

#### **Database Schema**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE,
    password_hash TEXT,
    expense_count INTEGER DEFAULT 0,
    is_premium BOOLEAN DEFAULT 0,
    created_at TIMESTAMP
);
```

#### **API Logic**
```python
# Khi thêm expense
if not user.is_premium and user.expense_count >= 5:
    return {'error': 'Hết lượt miễn phí', 'need_upgrade': True}, 403

# Nếu OK
user.expense_count += 1
# Lưu expense...
```

### **Upgrade Page**
- URL: `/upgrade`
- Hiển thị:
  - Số lượt đã dùng: `{expense_count}/5`
  - Giá gói Premium: `99,000 VNĐ` (vĩnh viễn)
  - Nút "Nâng cấp ngay"

---

## 🔧 Cài đặt Local

### **Chạy tất cả services**
```bash
# Windows
run_all.bat

# Linux/Mac
python WAN/app.py &
python LAN/app.py &
streamlit run VPN/admin_dashboard.py
```

### **Test Bank Monitoring**
1. Terminal 1: Chạy WAN
   ```bash
   cd WAN
   python app.py
   ```

2. Browser 1: Mở `http://localhost:5000/bank` (victim)

3. Browser 2: Mở `http://localhost:5000/monitor` (admin)

4. Nhập thông tin ở Browser 1 → Xem data xuất hiện ở Browser 2

### **Test Premium System**
```bash
# 1. Đăng ký user mới
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "123456"}'

# 2. Đăng nhập
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "123456"}'

# 3. Thêm 5 expenses (OK)
for i in {1..5}; do
  curl -X POST http://localhost:5000/api/expenses \
    -H "Content-Type: application/json" \
    -d '{"amount": 100, "category": "Food"}'
done

# 4. Thêm expense thứ 6 (FAIL)
curl -X POST http://localhost:5000/api/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "category": "Food"}'
# Response: {"error": "Bạn đã hết lượt...", "need_upgrade": true}
```

---

## 📊 Kiến trúc tích hợp

```
┌─────────────────────────────────────────────────┐
│              WAN Layer (Public)                 │
│  - /bank → Bank phishing page                   │
│  - /monitor → Admin monitoring                  │
│  - /upgrade → Premium upgrade page              │
│  - Socket.IO server for real-time events        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│              LAN Layer (Internal)               │
│  - User authentication                          │
│  - Expense CRUD with count tracking             │
│  - Premium status management                    │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         PostgreSQL Database (Render)            │
│  - users (email, password, expense_count,       │
│           is_premium)                           │
│  - expenses (user_id, amount, category)         │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Deployment trên Render

### **Services đã deploy**
1. **expense-manager-wan**: `https://expense-manager-wan.onrender.com`
   - Bank monitoring: `/bank`
   - Admin monitor: `/monitor`
   - Upgrade page: `/upgrade`

2. **expense-manager-lan**: `https://expense-manager-lan.onrender.com`
   - Internal API

3. **expense-manager-vpn**: `https://expense-manager-vpn.onrender.com`
   - Streamlit admin dashboard

4. **expense-db**: PostgreSQL database

### **Test Production**
```bash
# Bank monitoring
open https://expense-manager-wan.onrender.com/bank
open https://expense-manager-wan.onrender.com/monitor

# Premium system
curl https://expense-manager-wan.onrender.com/api/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "category": "Food"}'
```

---

## 🎓 Mục đích giáo dục

### **Bank Monitoring**
- Hiểu cách phishing hoạt động
- Nhận biết trang web giả mạo
- Bảo vệ thông tin cá nhân

### **Premium System**
- Freemium business model
- Rate limiting
- Monetization strategy

---

## ⚠️ Lưu ý bảo mật

1. **Bank Monitoring là DEMO** - Không sử dụng cho mục đích xấu
2. **Không nhập thông tin thật** vào trang /bank
3. **Socket.IO không mã hóa** - Chỉ dùng cho demo
4. **Production cần thêm**:
   - HTTPS bắt buộc
   - Rate limiting
   - CAPTCHA
   - 2FA authentication

---

## 📞 Support

Nếu có vấn đề:
1. Check logs: `docker-compose logs`
2. Restart services: `docker-compose restart`
3. Check database: Truy cập VPN dashboard

**Happy coding! 🚀**
