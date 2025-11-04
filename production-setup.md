# 🌍 Production Setup - Public WAN Access

## 🎯 **Mục tiêu**
Cho phép users từ MỌI MẠNG (4G, Wifi nhà, công ty, quán cà phê...) truy cập ứng dụng

## 🌐 **WAN Layer - Public Access**

### **Cách users truy cập:**
```
📱 User với 4G Viettel    → https://your-domain.com
💻 User với Wifi nhà      → https://your-domain.com  
🏢 User từ mạng công ty   → https://your-domain.com
☕ User từ quán cà phê    → https://your-domain.com
```

### **Không cần:**
- ❌ VPN để truy cập WAN
- ❌ Cấu hình mạng đặc biệt
- ❌ Whitelist IP
- ❌ Kết nối nội bộ

### **Chỉ cần:**
- ✅ Internet connection
- ✅ Web browser
- ✅ Đăng ký tài khoản

---

## 🚀 **Deployment Options**

### **Option 1: Cloud Hosting (Recommended)**
```bash
# Deploy lên AWS/GCP/Azure
# Domain: https://expense-manager.com
# SSL Certificate tự động
# CDN global
# Auto-scaling
```

### **Option 2: VPS với Domain**
```bash
# Thuê VPS (DigitalOcean, Vultr...)
# Mua domain name
# Setup SSL certificate
# Configure firewall
```

### **Option 3: Local với ngrok (Testing)**
```bash
# Chạy local
docker-compose up -d

# Expose ra internet
ngrok http 80

# Users truy cập: https://abc123.ngrok.io
```

---

## 🔧 **Production Configuration**

### **1. Environment Variables**
```bash
# .env.production
FLASK_ENV=production
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Domain configuration
DOMAIN_NAME=expense-manager.com
SSL_ENABLED=true

# Security
SECRET_KEY=super-secure-production-key
INTERNAL_SECRET=internal-production-secret
ADMIN_SECRET=admin-production-secret

# Database (Production)
DATABASE_URL=postgresql://prod_user:secure_pass@prod-db:5432/expense_prod

# Redis (Production)
REDIS_URL=redis://prod-redis:6379

# Rate limiting
RATE_LIMIT_ENABLED=true
MAX_REQUESTS_PER_HOUR=100
MAX_LOGIN_ATTEMPTS=5
```

### **2. Docker Compose Production**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  wan-app:
    build: ./WAN
    ports:
      - "80:5000"
      - "443:5000"
    environment:
      - FLASK_ENV=production
      - DOMAIN_NAME=${DOMAIN_NAME}
    volumes:
      - ./ssl:/app/ssl  # SSL certificates
    restart: always
    deploy:
      replicas: 3  # Multiple instances
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - wan-app
    restart: always
```

### **3. Nginx Configuration**
```nginx
# nginx.conf
upstream wan_app {
    server wan-app:5000;
}

server {
    listen 80;
    server_name expense-manager.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name expense-manager.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=20r/m;
    
    location / {
        proxy_pass http://wan_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://wan_app;
    }
    
    location /api/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://wan_app;
    }
}
```

---

## 🔒 **Security cho Public Access**

### **WAN Security Enhancements**
```python
# WAN/security.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

# Rate limiting với Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://redis:6379",
    default_limits=["200 per day", "50 per hour"]
)

# IP blocking cho suspicious activity
BLOCKED_IPS = set()
FAILED_ATTEMPTS = {}

def check_ip_security(ip):
    if ip in BLOCKED_IPS:
        return False
    
    # Check failed login attempts
    if ip in FAILED_ATTEMPTS:
        if FAILED_ATTEMPTS[ip] > 10:
            BLOCKED_IPS.add(ip)
            return False
    
    return True

# Geo-blocking (optional)
ALLOWED_COUNTRIES = ['VN', 'US', 'SG']  # Vietnam, US, Singapore

def check_geo_location(ip):
    # Use GeoIP service to check country
    # Block if not in allowed countries
    pass
```

### **Input Validation**
```python
# WAN/validators.py
import re
from flask import request

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    # Minimum 8 characters, at least 1 letter and 1 number
    if len(password) < 8:
        return False
    if not re.search(r'[A-Za-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True

def sanitize_input(data):
    # Remove potential XSS/SQL injection
    dangerous_chars = ['<', '>', '"', "'", '&', 'script', 'SELECT', 'DROP']
    for char in dangerous_chars:
        data = data.replace(char, '')
    return data
```

---

## 📱 **Mobile-Friendly WAN**

### **Responsive Design**
```html
<!-- WAN/templates/base.html -->
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    
    <title>Expense Manager</title>
    
    <!-- PWA Support -->
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#4CAF50">
    
    <!-- Mobile optimized CSS -->
    <style>
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .btn { width: 100%; margin: 5px 0; }
            input { font-size: 16px; } /* Prevent zoom on iOS */
        }
    </style>
</head>
<body>
    <!-- Mobile-first design -->
</body>
</html>
```

### **PWA Manifest**
```json
// WAN/static/manifest.json
{
  "name": "Expense Manager",
  "short_name": "ExpenseApp",
  "description": "Quản lý chi tiêu cá nhân",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#4CAF50",
  "icons": [
    {
      "src": "/static/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/icon-512.png", 
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

---

## 🌍 **Global CDN Setup**

### **CloudFlare Configuration**
```bash
# Thêm domain vào CloudFlare
# Enable:
- SSL/TLS Full (strict)
- Always Use HTTPS
- Auto Minify (CSS, JS, HTML)
- Brotli Compression
- Caching Level: Standard

# Security Rules:
- Block countries: None (allow global)
- Challenge on high threat score
- Rate limiting: 100 req/min per IP
```

### **Performance Optimization**
```python
# WAN/app.py - Add caching
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://redis:6379'
})

@app.route('/dashboard')
@login_required
@cache.cached(timeout=300)  # Cache 5 minutes
def dashboard():
    # Dashboard code...
    pass
```

---

## 📊 **Monitoring Public Access**

### **Analytics**
```python
# WAN/analytics.py
import geoip2.database
from collections import defaultdict

# Track user locations
user_locations = defaultdict(int)
daily_active_users = defaultdict(set)

def track_user_access(ip, user_id=None):
    try:
        # Get country from IP
        reader = geoip2.database.Reader('/app/GeoLite2-Country.mmdb')
        response = reader.country(ip)
        country = response.country.iso_code
        
        user_locations[country] += 1
        
        if user_id:
            today = datetime.now().date()
            daily_active_users[today].add(user_id)
            
    except:
        pass

# Usage stats for admin
def get_usage_stats():
    return {
        'countries': dict(user_locations),
        'daily_users': {str(k): len(v) for k, v in daily_active_users.items()}
    }
```

---

## 🚀 **Quick Deploy Commands**

### **Development (Local + ngrok)**
```bash
# 1. Start local
docker-compose up -d

# 2. Expose to internet
ngrok http 80

# 3. Share URL với users
# Users có thể truy cập từ bất kỳ mạng nào
```

### **Production (VPS)**
```bash
# 1. Setup VPS
ssh root@your-server-ip

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 3. Clone & deploy
git clone your-repo
cd expense-manager
cp .env.example .env.production
docker-compose -f docker-compose.prod.yml up -d

# 4. Setup domain
# Point DNS A record: your-domain.com → server-ip
```

### **Cloud (AWS/GCP)**
```bash
# Use managed services:
- AWS ECS/Fargate for containers
- AWS RDS for database  
- AWS CloudFront for CDN
- AWS Route 53 for DNS
- AWS Certificate Manager for SSL
```

---

## ✅ **Kết quả**

Sau khi setup, users có thể:

1. **Từ điện thoại 4G**: Mở browser → https://your-domain.com → Đăng ký/Đăng nhập
2. **Từ Wifi nhà**: Mở laptop → https://your-domain.com → Sử dụng bình thường  
3. **Từ mạng công ty**: Mở máy tính → https://your-domain.com → Không bị chặn
4. **Từ quán cà phê**: Mở điện thoại → https://your-domain.com → Hoạt động tốt

**Không cần cài đặt gì thêm, chỉ cần internet + browser!**