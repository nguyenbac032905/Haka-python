# API Documentation

Base URL:

```text
http://127.0.0.1:3002
```

## Chạy server

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Mục tiêu của backend này

- Khớp trực tiếp với frontend trong `haka-frontend.zip`
- Chỉ giữ các resource frontend đang dùng
- Trả dữ liệu theo kiểu `json-server`
- Tách route/controller theo từng resource

## Các resource đang hỗ trợ

- `accounts`
- `users`
- `product_categories`
- `products`
- `orders`
- `order_items`

Các API cũ không còn dùng bởi frontend đã bị bỏ:

- `/accounts/login`
- `/users/login`
- `/products/search`
- `/products/slug/:slug`
- `/product-categories/tree`
- toàn bộ API `cart`, `comments`, `orders/from-cart`, `orders/:id/detail`, `users/:id/orders`
- route generic động `/<table>` cho mọi bảng

## Cấu trúc source

- `controllers/accountController.py`
- `controllers/userController.py`
- `controllers/productController.py`
- `controllers/productCategoryController.py`
- `controllers/orderController.py`
- `controllers/orderItemController.py`
- `routes/accountRoute.py`
- `routes/userRoute.py`
- `routes/productRoute.py`
- `routes/productCategoryRoute.py`
- `routes/orderRoute.py`
- `routes/orderItemRoute.py`

## Quy ước response kiểu json-server

### 1. Lấy danh sách

```http
GET /products
GET /products?deleted=false
GET /accounts?email=admin@gmail.com&password=123456
GET /order_items?order_id=10
```

Response:

```json
[
  {
    "id": 1
  }
]
```

### 2. Lấy chi tiết

```http
GET /products/1
GET /orders/3
```

Response:

```json
{
  "id": 1
}
```

### 3. Tạo mới

```http
POST /products
Content-Type: application/json
```

Response:

```json
{
  "id": 1
}
```

### 4. Cập nhật một phần

```http
PATCH /orders/1
Content-Type: application/json
```

Response:

```json
{
  "id": 1
}
```

### 5. Xóa

```http
DELETE /products/1
```

Nếu bảng có cột `deleted`, backend sẽ soft delete và trả về object sau khi cập nhật.

## Query params được hỗ trợ

- `field=value`: lọc chính xác theo cột
- `_q`: tìm gần đúng trên các cột text
- `_sort`: sắp xếp theo cột
- `_order=ASC|DESC`
- `_page`
- `_limit`

Ví dụ:

```http
GET /products?deleted=false&_sort=id&_order=DESC&_page=1&_limit=10
```

## Tương thích riêng với frontend hiện tại

### `users.token`

Trong SQLite, bảng `users` đang dùng cột `tokenUser`, nhưng frontend gọi:

```http
GET /users?email=abc@gmail.com&token=xyz
```

Backend đã map tự động:

- query `token` -> cột DB `tokenUser`
- response trả `token`
- `POST/PATCH /users` nhận cả field `token`

### Field dư trong body

Frontend hiện có chỗ gửi field không tồn tại trong DB, ví dụ `sold` khi tạo `product_categories`.

Backend sẽ:

- bỏ qua field dư
- chỉ ghi các field thật sự tồn tại trong bảng

Điều này giúp hành vi gần với `json-server` và tránh lỗi không cần thiết.
