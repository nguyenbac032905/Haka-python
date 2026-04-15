# API Documentation

Base URL mặc định:

```text
http://127.0.0.1:5001
```

## Chạy server

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Ghi chú chung

- API đang dùng SQLite tại `database/haka.db`.
- Các bảng được hỗ trợ generic CRUD: `accounts`, `users`, `product_categories`, `products`, `carts`, `cart_items`, `orders`, `order_items`, `comments`.
- URL alias cũng được hỗ trợ:
  - `product-categories` -> `product_categories`
  - `cart-items` -> `cart_items`
  - `order-items` -> `order_items`
- Các endpoint generic chỉ thao tác trên bảng đã được whitelist.
- `DELETE` sẽ ưu tiên soft delete nếu bảng có cột `deleted`.

## 1. Generic CRUD kiểu JSON Server

### 1.1 Lấy toàn bộ dữ liệu

```http
GET /{table}
```

Ví dụ:

```http
GET /accounts
GET /products
```

Response:

```json
[
  {
    "id": 1,
    "fullName": "Admin",
    "email": "admin@gmail.com",
    "password": "123456",
    "token": null,
    "phone": null,
    "avatar": null,
    "status": "active",
    "deleted": 0,
    "deletedAt": null,
    "createdAt": "2026-04-15 10:00:00",
    "updatedAt": "2026-04-15 10:00:00"
  }
]
```

### 1.2 Lọc theo điều kiện query params

```http
GET /{table}?key=value&key2=value2
```

Backend xử lý:

- Lọc theo điều kiện `AND`
- So sánh bằng `=`

Ví dụ:

```http
GET /accounts?email=admin@gmail.com&password=123456
```

### 1.3 Tìm kiếm nhanh, sort, phân trang cho generic API

Các query params hỗ trợ thêm:

- `_q`: tìm kiếm gần đúng trên các cột text
- `_sort`: tên cột cần sắp xếp
- `_order`: `ASC` hoặc `DESC`
- `_page`: trang hiện tại
- `_limit`: số bản ghi tối đa

Ví dụ:

```http
GET /products?_q=iphone&_sort=price&_order=DESC&_page=1&_limit=10
```

### 1.4 Lấy theo ID

```http
GET /{table}/{id}
```

Ví dụ:

```http
GET /accounts/1
GET /products/5
```

### 1.5 Tạo mới dữ liệu

```http
POST /{table}
Content-Type: application/json
```

Ví dụ:

```json
{
  "fullName": "New User",
  "email": "user@gmail.com",
  "password": "123456"
}
```

Backend xử lý:

- Tự generate `id`
- Nếu bảng có cột `status` nhưng không có default DB thì tự gán `active`
- Nếu bảng có cột `deleted` thì tự gán `0`

Ví dụ:

```http
POST /accounts
```

Response:

```json
{
  "id": 2,
  "fullName": "New User",
  "email": "user@gmail.com",
  "password": "123456",
  "token": null,
  "phone": null,
  "avatar": null,
  "status": "active",
  "deleted": 0,
  "deletedAt": null,
  "createdAt": "2026-04-15 10:00:00",
  "updatedAt": "2026-04-15 10:00:00"
}
```

### 1.6 Cập nhật 1 phần dữ liệu

```http
PATCH /{table}/{id}
Content-Type: application/json
```

Ví dụ:

```http
PATCH /accounts/1
```

Body:

```json
{
  "status": "inactive"
}
```

Backend xử lý:

- Chỉ update field được gửi lên
- Không overwrite toàn bộ object
- Nếu bảng có cột `updatedAt` thì tự cập nhật thời gian

### 1.7 Xóa dữ liệu

```http
DELETE /{table}/{id}
```

Ví dụ:

```http
DELETE /products/3
```

## 2. Authentication

### 2.1 Đăng nhập account admin

```http
POST /accounts/login
Content-Type: application/json
```

Body:

```json
{
  "email": "admin@gmail.com",
  "password": "123456"
}
```

### 2.2 Đăng nhập user

```http
POST /users/login
Content-Type: application/json
```

Body:

```json
{
  "email": "user@gmail.com",
  "password": "123456"
}
```

## 3. Product APIs

### 3.1 Tìm kiếm sản phẩm nâng cao

```http
GET /products/search
```

Query params hỗ trợ:

- `q`: từ khóa
- `categoryId`: id danh mục
- `minPrice`: giá tối thiểu
- `maxPrice`: giá tối đa
- `inStock`: `true` hoặc `false`
- `status`: ví dụ `active`
- `sort`: `price`, `createdAt`, `sold`, `title`, `position`
- `order`: `ASC` hoặc `DESC`
- `page`: trang hiện tại
- `limit`: số item mỗi trang

Ví dụ:

```http
GET /products/search?q=iphone&categoryId=1&minPrice=10000000&maxPrice=40000000&inStock=true&sort=price&order=ASC&page=1&limit=12
```

Response item có thêm:

- `categoryTitle`
- `categorySlug`
- `finalPrice`

### 3.2 Lấy sản phẩm theo slug

```http
GET /products/slug/{slug}
```

Ví dụ:

```http
GET /products/slug/iphone-15-pro-max
```

Response có thêm:

- `categoryTitle`
- `categorySlug`
- `finalPrice`
- `commentsCount`
- `averageRating`

## 4. Category APIs

### 4.1 Lấy cây danh mục

```http
GET /product-categories/tree
```

Response trả về danh mục nhiều cấp qua field `children`.

## 5. Comment APIs

### 5.1 Lấy comment theo sản phẩm

```http
GET /products/{product_id}/comments
```

Ví dụ:

```http
GET /products/1/comments
```

Response:

```json
{
  "product": {
    "id": 1,
    "title": "iPhone 15 Pro Max",
    "slug": "iphone-15-pro-max"
  },
  "summary": {
    "count": 2,
    "averageRating": 4.5
  },
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "product_id": 1,
      "rating": 5,
      "content": "Máy đẹp",
      "image": null,
      "deleted": 0,
      "createdAt": "2026-04-15 10:00:00",
      "updatedAt": "2026-04-15 10:00:00",
      "userFullName": "Nguyen Van A",
      "userAvatar": null
    }
  ]
}
```

### 5.2 Tạo mới hoặc cập nhật review

```http
POST /products/{product_id}/comments
Content-Type: application/json
```

Body:

```json
{
  "user_id": 1,
  "rating": 5,
  "content": "Sản phẩm rất tốt",
  "image": "https://example.com/review.jpg"
}
```

Ghi chú:

- Một user chỉ có 1 review cho mỗi sản phẩm.
- Nếu đã tồn tại review thì API sẽ update review cũ.

## 6. Cart APIs

### 6.1 Lấy giỏ hàng của user

```http
GET /users/{user_id}/cart
```

Ví dụ:

```http
GET /users/1/cart
```

Response gồm:

- `cart`: thông tin cart
- `items`: danh sách item
- `summary`: tổng tiền, tổng số lượng, discount, grand total

### 6.2 Thêm sản phẩm vào giỏ hàng

```http
POST /users/{user_id}/cart/items
Content-Type: application/json
```

Body:

```json
{
  "product_id": 1,
  "quantity": 2
}
```

Ghi chú:

- Nếu sản phẩm đã có trong giỏ thì cộng dồn số lượng.
- Có kiểm tra tồn kho.

### 6.3 Cập nhật số lượng item trong giỏ

```http
PATCH /users/{user_id}/cart/items/{item_id}
Content-Type: application/json
```

Body:

```json
{
  "quantity": 3
}
```

Ghi chú:

- Nếu `quantity <= 0` thì item sẽ bị xóa khỏi giỏ.

### 6.4 Xóa item khỏi giỏ

```http
DELETE /users/{user_id}/cart/items/{item_id}
```

## 7. Order APIs

### 7.1 Tạo đơn hàng từ giỏ

```http
POST /orders/from-cart
Content-Type: application/json
```

Body:

```json
{
  "user_id": 1,
  "fullName": "Nguyen Van A",
  "phone": "0912345678",
  "address": "12 Nguyen Trai, HCM",
  "paymentMethod": "cod"
}
```

Backend xử lý:

- Lấy toàn bộ `cart_items` của user
- Tạo `orders`
- Tạo `order_items`
- Trừ `stock`
- Tăng `sold`
- Xóa item khỏi cart sau khi tạo đơn thành công

### 7.2 Lấy chi tiết đơn hàng

```http
GET /orders/{order_id}/detail
```

Response gồm:

- `order`
- `items`
- `summary`

### 7.3 Lấy lịch sử đơn hàng của user

```http
GET /users/{user_id}/orders
```

### 7.4 Cập nhật trạng thái đơn hàng

```http
PATCH /orders/{order_id}/status
Content-Type: application/json
```

Body mẫu:

```json
{
  "status": "confirmed",
  "paymentStatus": "paid"
}
```

Field được phép update:

- `status`
- `paymentStatus`
- `paymentMethod`
- `phone`
- `address`

## 8. Dữ liệu mẫu nên tạo trước khi test

Thứ tự seed đề xuất để test Postman:

1. `POST /accounts`
2. `POST /users`
3. `POST /product-categories`
4. `POST /products`
5. `POST /users/{user_id}/cart/items`
6. `POST /orders/from-cart`
7. `POST /products/{product_id}/comments`

## 9. Bộ request Postman gợi ý

### Tạo user

```http
POST /users
```

```json
{
  "fullName": "Nguyen Van A",
  "email": "user1@gmail.com",
  "password": "123456",
  "phone": "0912345678",
  "status": "active"
}
```

### Tạo danh mục

```http
POST /product-categories
```

```json
{
  "title": "iPhone",
  "description": "Danh mục iPhone",
  "thumbnail": "https://example.com/iphone.jpg",
  "status": "active",
  "position": 1,
  "slug": "iphone"
}
```

### Tạo sản phẩm

```http
POST /products
```

```json
{
  "title": "iPhone 15 Pro Max",
  "product_category_id": 1,
  "description": "Điện thoại cao cấp",
  "content": "Chip mạnh, camera đẹp",
  "price": 32990000,
  "discountPercentage": 5,
  "stock": 20,
  "thumbnail": "https://example.com/iphone15promax.jpg",
  "status": "active",
  "position": 1,
  "slug": "iphone-15-pro-max"
}
```

### Thêm vào giỏ hàng

```http
POST /users/1/cart/items
```

```json
{
  "product_id": 1,
  "quantity": 1
}
```

### Tạo đơn hàng

```http
POST /orders/from-cart
```

```json
{
  "user_id": 1,
  "fullName": "Nguyen Van A",
  "phone": "0912345678",
  "address": "12 Nguyen Trai, HCM",
  "paymentMethod": "cod"
}
```

### Tạo review

```http
POST /products/1/comments
```

```json
{
  "user_id": 1,
  "rating": 5,
  "content": "Rất hài lòng"
}
```

## 10. Mã lỗi thường gặp

- `400`: Body sai định dạng, thiếu field, field không hợp lệ, vượt tồn kho
- `401`: Sai email hoặc password
- `404`: Không tìm thấy dữ liệu, user, product, order, item

