# ShopZone Final Demonstration Script & Verification Walkthrough

This document outlines the step-by-step walkthrough for demonstrating all 12 core full-stack features of the ShopZone e-commerce platform.

---

## 1. System Readiness Checklist

Before beginning the demonstration, verify that the supporting services and applications are active:

| Service | Port / Process | Status Command | Expected Output |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | Port `5432` | Connected | Tables `users`, `products`, `orders`, `order_items` exist |
| **Redis** | Port `6379` | `.\redis\redis-cli.exe ping` | `PONG` |
| **FastAPI Backend** | Port `8000` | `curl http://127.0.0.1:8000/health` | `{"status":"ok","service":"shopzone-api","version":"1.0.0"}` |
| **Celery Worker** | Background process | `py -3.14 -m celery ... inspect ping` | `celery@...: OK` |
| **Frontend UI** | Port `5173` or `4173` | Browser visit | Clean landing page, live WebSocket badge |

---

## 2. Demo User Credentials

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@shopzone.dev` | `Admin@12345` | Product creation, CSV bulk import, global orders, admin dashboard |
| **Customer A** | `customer@shopzone.dev` | `Customer@12345` | Catalog browsing, cart, checkout, view own order history |
| **Customer B** | `shopper2@shopzone.dev` | `Customer@12345` | Distinct tenant used to demonstrate BOLA/IDOR protection |

---

## 3. The 12 End-to-End Workflows

### Workflow 1: User Registration & Login
1. **Navigate to:** `http://localhost:5173/login`
2. **Action:** Register a new user or log in with `customer@shopzone.dev`.
3. **Verify:**
   - Client receives a signed JWT `access_token` and user profile.
   - Password is never stored in plain text (verified PBKDF2-SHA256 hash in PostgreSQL).
   - SlowAPI enforces rate limiting: Attempting > 5 logins in 60 seconds returns HTTP `429 Too Many Requests` with `Retry-After`.

---

### Workflow 2: JWT Authentication & Protected Routes
1. **Action:** Attempt to access `http://localhost:5173/orders` while logged out.
2. **Verify:**
   - The user is redirected to `/login` with an informational redirect prompt.
3. **Action:** Log in as customer.
4. **Verify:**
   - Navigating to `/orders` succeeds. Bearer token is automatically attached to API calls via the TanStack Query / Axios client.

---

### Workflow 3: Product Listing, Search & Fuzzy Filtering
1. **Navigate to:** `http://localhost:5173/`
2. **Action:** Enter a typo or partial search term like `lap` or `headphon` into the search bar.
3. **Verify:**
   - PostgreSQL English Full-Text Search and trigram fuzzy matching return relevant products instantaneously.
   - Clear search button resets the view cleanly.
   - Product images load quickly using optimized Unsplash WebP thumbnails (~19 KB).

---

### Workflow 4: Cart Operations & Totals
1. **Action:** Click "Add to Cart" on multiple items.
2. **Navigate to:** `http://localhost:5173/cart`
3. **Verify:**
   - Line items, quantities, and subtotal calculations update in real time via Zustand store.
   - Decrementing to 0 removes the item; incrementing reflects updated pricing immediately.

---

### Workflow 5: Order Creation & Concurrency-Safe Stock Validation
1. **Action:** Proceed to `/checkout`, enter shipping details, and submit order.
2. **Verify:**
   - Backend performs atomic transaction: verifies product stock, decrements inventory, creates order and order items.
   - If stock is insufficient, transaction rolls back cleanly with HTTP 400 and clear error detail.
   - Order confirmation displays Order ID and details.

---

### Workflow 6: PostgreSQL Persistence
1. **Action:** Inspect the database after checkout:
   ```sql
   SELECT id, customer_id, total_amount, status, created_at FROM orders ORDER BY id DESC LIMIT 1;
   ```
2. **Verify:** Order and corresponding `order_items` are persisted with relational integrity.

---

### Workflow 7: Redis Caching & Cache Invalidation
1. **Action:** Request `/products`. First request queries database and seeds Redis cache (`product:catalog:all`).
2. **Verify:** Subsequent queries resolve directly from Redis memory in < 15 ms.
3. **Action:** Admin adds or updates a product via `/manage`.
4. **Verify:** Backend automatically evicts the Redis cache key, ensuring fresh data on the next catalog request.

---

### Workflow 8: Celery Background Tasks & Status Polling
1. **Navigate to:** `http://localhost:5173/tasks`
2. **Action:** Click "Trigger Sample Background Job" (e.g. data synchronization simulation).
3. **Verify:**
   - HTTP 202 Accepted returned with `task_id`.
   - Celery worker picks up job asynchronously via Redis broker.
   - Frontend polls `GET /tasks/{task_id}` and shows `PENDING` -> `SUCCESS` with job results.

---

### Workflow 9: PDF Invoice Generation
1. **Navigate to:** `http://localhost:5173/orders`
2. **Action:** On a completed order, click "Download Invoice PDF".
3. **Verify:**
   - Asynchronous ReportLab PDF generation executes via Celery.
   - Formatted PDF containing order summary, line items, and tax breakdown is delivered to the browser.

---

### Workflow 10: CSV Bulk Product Import (Admin Only)
1. **Log in as:** `admin@shopzone.dev`
2. **Navigate to:** `http://localhost:5173/admin`
3. **Action:** Upload a sample CSV file containing new products (`name,price,category,stock,image`).
4. **Verify:**
   - Backend dispatches `bulk_import_products_csv_task` to Celery.
   - Admin receives progress notification; catalog updates immediately upon worker completion.

---

### Workflow 11: Real-Time WebSocket Order Updates
1. **Verify Header:** The header displays the live WebSocket status badge (`Live` with green dot).
2. **Action:** Place a new order in one window while keeping the orders dashboard open in another.
3. **Verify:**
   - Order status broadcast sent via WebSocket (`ws://localhost:8000/ws`).
   - Client receives real-time event without requiring manual browser refresh.

---

### Workflow 12: Admin vs Customer Role-Based Access Control (RBAC & BOLA/IDOR)
1. **Log in as:** Customer (`customer@shopzone.dev`).
2. **Action:**
   - Attempt to access `/manage` or `/admin` -> Route is protected, access forbidden.
   - Attempt to query another user's order details (`GET /orders/{other_customer_order_id}`) via API client.
3. **Verify:**
   - Backend responds with HTTP `403 Forbidden` (`detail: "You do not have permission to view or manage this order"`).
   - Demonstrates complete OWASP BOLA / IDOR protection.
4. **Log in as:** Admin (`admin@shopzone.dev`).
5. **Verify:**
   - Admin can view all orders and manage products successfully.
