import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Page config
st.set_page_config(
    page_title="🔐 Admin Panel - Expense Manager", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
LAN_API_URL = os.getenv('LAN_API_URL', 'http://lan-app:5001')
ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'admin-secret-key')

# Helper functions
def call_lan_api(endpoint, method='GET', data=None):
    """Gọi LAN API với admin credentials"""
    headers = {'Admin-Secret': ADMIN_SECRET}
    
    try:
        if method == 'GET':
            response = requests.get(f"{LAN_API_URL}{endpoint}", headers=headers)
        elif method == 'POST':
            response = requests.post(f"{LAN_API_URL}{endpoint}", json=data, headers=headers)
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code}"
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

def verify_admin_credentials(username, password):
    """Verify admin login"""
    # Simple admin check - trong production nên dùng database
    admin_users = {
        'admin': 'admin123',
        'superuser': 'super456'
    }
    return admin_users.get(username) == password

# ===== AUTHENTICATION =====
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Admin Authentication")
    st.warning("⚠️ Chỉ dành cho Administrator. Yêu cầu kết nối VPN.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Đăng nhập Admin")
        
        with st.form("admin_login"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔑 Password", type="password")
            submit = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submit:
                if verify_admin_credentials(username, password):
                    st.session_state.authenticated = True
                    st.session_state.admin_user = username
                    st.success("✅ Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("❌ Sai username hoặc password!")
    
    st.info("💡 **Lưu ý bảo mật**: Admin panel chỉ truy cập được qua VPN. Đảm bảo bạn đã kết nối VPN trước khi đăng nhập.")
    st.stop()

# ===== MAIN DASHBOARD =====
st.title("🎯 Admin Dashboard - Expense Management System")
st.sidebar.success(f"👋 Xin chào, **{st.session_state.admin_user}**")

if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.rerun()

# Sidebar navigation
st.sidebar.title("📋 Navigation")
page = st.sidebar.selectbox("Chọn trang", [
    "📊 System Overview",
    "👥 User Management", 
    "💰 All Expenses",
    "📈 Analytics",
    "⚙️ System Management"
])

# ===== PAGE: SYSTEM OVERVIEW =====
if page == "📊 System Overview":
    st.header("📊 System Overview")
    
    # Get system stats
    stats, error = call_lan_api('/admin/system_stats')
    
    if error:
        st.error(f"❌ Không thể kết nối LAN API: {error}")
        st.stop()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "👥 Total Users", 
            f"{stats['total_users']:,}",
            delta="+15 hôm nay"
        )
    
    with col2:
        st.metric(
            "💰 Total Expenses", 
            f"{stats['total_expenses']:,}",
            delta="+234 hôm nay"
        )
    
    with col3:
        st.metric(
            "💵 Total Amount", 
            f"{stats['total_amount']:,.0f} VNĐ"
        )
    
    with col4:
        st.metric(
            "🟢 Active Now", 
            stats['active_users']
        )
    
    st.divider()
    
    # Recent activities (mock data for demo)
    st.subheader("🕒 Recent System Activities")
    
    activities_data = [
        {"Time": "2024-01-15 14:30", "Event": "USER_LOGIN", "User": "user@email.com", "Details": "Successful login"},
        {"Time": "2024-01-15 14:25", "Event": "EXPENSE_ADDED", "User": "john@email.com", "Details": "Added expense: 50,000 VNĐ - Ăn uống"},
        {"Time": "2024-01-15 14:20", "Event": "USER_REGISTERED", "User": "newuser@email.com", "Details": "New user registration"},
        {"Time": "2024-01-15 14:15", "Event": "EXPENSE_ADDED", "User": "mary@email.com", "Details": "Added expense: 200,000 VNĐ - Mua sắm"},
    ]
    
    df_activities = pd.DataFrame(activities_data)
    st.dataframe(df_activities, use_container_width=True)

# ===== PAGE: USER MANAGEMENT =====
elif page == "👥 User Management":
    st.header("👥 User Management")
    st.caption("⚠️ **Admin có thể xem và quản lý TẤT CẢ users trong hệ thống**")
    
    # Search
    search_email = st.text_input("🔍 Tìm user theo email")
    
    # Get all users
    users_data, error = call_lan_api('/admin/all_users')
    
    if error:
        st.error(f"❌ Không thể tải danh sách users: {error}")
        st.stop()
    
    # Filter users
    if search_email:
        users_data = [u for u in users_data if search_email.lower() in u['email'].lower()]
    
    st.subheader(f"📋 Danh sách Users ({len(users_data)} users)")
    
    # Display users
    for user in users_data:
        with st.expander(f"📧 {user['email']} - {'✅ Active' if user['is_active'] else '❌ Banned'}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**User ID:** `{user['id']}`")
                st.write(f"**Email:** {user['email']}")
                st.write(f"**Joined:** {user['created_at']}")
                st.write(f"**Status:** {'✅ Active' if user['is_active'] else '❌ Banned'}")
            
            with col2:
                st.write(f"**Total Expenses:** {user['expense_count']} giao dịch")
                st.write(f"**Total Spent:** {user['total_spent']:,.0f} VNĐ")
                
                # Admin actions
                if user['is_active']:
                    if st.button(f"🚫 Ban User", key=f"ban_{user['id']}"):
                        result, error = call_lan_api('/admin/ban_user', 'POST', {'user_id': user['id']})
                        if error:
                            st.error(f"❌ Lỗi: {error}")
                        else:
                            st.success(f"✅ Đã ban user {user['email']}")
                            st.rerun()

# ===== PAGE: ALL EXPENSES =====
elif page == "💰 All Expenses":
    st.header("💰 All Expenses in System")
    st.caption("⚠️ **Admin có thể xem TẤT CẢ chi tiêu của TẤT CẢ users**")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        filter_email = st.text_input("🔍 Filter by user email")
    with col2:
        filter_category = st.selectbox("📂 Filter by category", 
            ["All", "Ăn uống", "Di chuyển", "Mua sắm", "Giải trí", "Khác"])
    
    # Get all expenses
    expenses_data, error = call_lan_api('/admin/all_expenses')
    
    if error:
        st.error(f"❌ Không thể tải expenses: {error}")
        st.stop()
    
    # Convert to DataFrame
    df_expenses = pd.DataFrame(expenses_data)
    
    if not df_expenses.empty:
        # Apply filters
        if filter_email:
            df_expenses = df_expenses[df_expenses['user_email'].str.contains(filter_email, case=False, na=False)]
        
        if filter_category != "All":
            df_expenses = df_expenses[df_expenses['category'] == filter_category]
        
        st.subheader(f"📊 Expenses Data ({len(df_expenses)} records)")
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Amount", f"{df_expenses['amount'].sum():,.0f} VNĐ")
        with col2:
            st.metric("📊 Avg Amount", f"{df_expenses['amount'].mean():,.0f} VNĐ")
        with col3:
            st.metric("🔢 Total Records", len(df_expenses))
        
        # Data table
        st.dataframe(
            df_expenses[['user_email', 'amount', 'category', 'description', 'created_at']],
            use_container_width=True
        )
        
        # Export button
        if st.button("📥 Export to CSV"):
            csv = df_expenses.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"all_expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("📭 Chưa có dữ liệu expenses")

# ===== PAGE: ANALYTICS =====
elif page == "📈 Analytics":
    st.header("📈 System Analytics")
    st.caption("📊 **Phân tích toàn hệ thống - chỉ Admin mới thấy được**")
    
    # Get expenses data for analytics
    expenses_data, error = call_lan_api('/admin/all_expenses')
    
    if error:
        st.error(f"❌ Không thể tải dữ liệu: {error}")
        st.stop()
    
    if expenses_data:
        df = pd.DataFrame(expenses_data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date
        
        # Expenses by Category
        st.subheader("📊 Chi tiêu theo danh mục")
        category_stats = df.groupby('category')['amount'].sum().sort_values(ascending=False)
        
        fig_pie = px.pie(
            values=category_stats.values, 
            names=category_stats.index,
            title="Phân bố chi tiêu theo danh mục"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Daily expenses trend
        st.subheader("📈 Xu hướng chi tiêu theo ngày")
        daily_stats = df.groupby('date')['amount'].sum().reset_index()
        
        fig_line = px.line(
            daily_stats, 
            x='date', 
            y='amount',
            title="Tổng chi tiêu hàng ngày"
        )
        st.plotly_chart(fig_line, use_container_width=True)
        
        # Top spenders
        st.subheader("🏆 Top Users chi tiêu nhiều nhất")
        top_spenders = df.groupby('user_email')['amount'].agg(['sum', 'count']).sort_values('sum', ascending=False).head(10)
        top_spenders.columns = ['Tổng chi tiêu (VNĐ)', 'Số giao dịch']
        st.dataframe(top_spenders, use_container_width=True)
    
    else:
        st.info("📭 Chưa có dữ liệu để phân tích")

# ===== PAGE: SYSTEM MANAGEMENT =====
elif page == "⚙️ System Management":
    st.header("⚙️ System Management")
    st.caption("🔧 **Quản lý hệ thống - chỉ dành cho Admin**")
    
    # Database management
    st.subheader("🗄️ Database Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Initialize Database", use_container_width=True):
            result, error = call_lan_api('/init_db', 'POST')
            if error:
                st.error(f"❌ Lỗi: {error}")
            else:
                st.success("✅ Database đã được khởi tạo!")
    
    with col2:
        if st.button("💾 Backup Database", use_container_width=True):
            st.info("🔄 Đang thực hiện backup... (Demo)")
            # Trong thực tế sẽ gọi API backup
    
    st.divider()
    
    # System monitoring (mock data)
    st.subheader("📊 Server Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💻 CPU Usage", "45%", delta="-5%")
    with col2:
        st.metric("🧠 RAM Usage", "67%", delta="+3%")
    with col3:
        st.metric("💽 Disk Usage", "23%", delta="+1%")
    
    # System logs (mock)
    st.subheader("📋 System Logs")
    
    log_type = st.selectbox("📂 Log Type", ["All", "Errors", "Warnings", "Info"])
    
    logs_data = [
        {"Timestamp": "2024-01-15 14:30:25", "Level": "INFO", "Message": "User login successful: user@email.com"},
        {"Timestamp": "2024-01-15 14:29:15", "Level": "WARNING", "Message": "High CPU usage detected: 85%"},
        {"Timestamp": "2024-01-15 14:28:45", "Level": "ERROR", "Message": "Database connection timeout"},
        {"Timestamp": "2024-01-15 14:27:30", "Level": "INFO", "Message": "Expense added successfully"},
    ]
    
    for log in logs_data:
        if log_type == "All" or log_type == log["Level"].title() + "s":
            if log["Level"] == "ERROR":
                st.error(f"🔴 [{log['Timestamp']}] {log['Message']}")
            elif log["Level"] == "WARNING":
                st.warning(f"🟡 [{log['Timestamp']}] {log['Message']}")
            else:
                st.info(f"🔵 [{log['Timestamp']}] {log['Message']}")

# Footer
st.divider()
st.caption("🔐 **Admin Panel** - Chỉ truy cập qua VPN | Expense Management System")
st.caption(f"👤 Logged in as: **{st.session_state.admin_user}** | 🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")