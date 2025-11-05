# Camera Demo - Mô phỏng tấn công

## Cài đặt và chạy

```bash
cd camera-demo
npm install
npm start
```

## Sử dụng

1. **Người dùng**: Truy cập `http://localhost:3000`
   - Đăng nhập bằng bất kỳ username/password nào
   - Camera sẽ được kích hoạt ngầm

2. **Admin**: Truy cập `http://localhost:3000/admin`
   - Xem camera của tất cả người dùng đang online
   - Theo dõi real-time

## Cách hoạt động

- Khi người dùng đăng nhập, camera được kích hoạt mà không thông báo
- Video stream được gửi đến admin dashboard qua WebSocket
- Admin có thể theo dõi nhiều người dùng cùng lúc

## Lưu ý

- Demo chỉ hoạt động trên HTTPS hoặc localhost
- Cần cho phép camera access trên browser