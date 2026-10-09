# Day 16 backend

FastAPI backend using PostgreSQL through psycopg. SQLite is available as an
explicit local-development option; the database engine is never silently
changed when PostgreSQL is unavailable.

## Setup

Install the dependencies from `requirements.txt`, copy `.env.example` to `.env`,
and configure the PostgreSQL connection variables. Set `JWT_SECRET_KEY` to a
stable, randomly generated secret with at least 32 bytes. Keep `.env` private;
changing the key invalidates all existing login tokens. The app loads the
database schema and applies additive migrations at startup. An empty database
is populated with the starter product catalog; users register through the app.

Run from this directory with `uvicorn main:app --reload`. The current database
defaults are `sqlight` for `PGDATABASE` and `Thriveni` for `PGUSER` if those
variables are omitted.

### Local development without PostgreSQL

If PostgreSQL is not installed or running, explicitly set
`DATABASE_ENGINE=sqlite` in `.env`. This uses the existing SQLite database at
`ecommerce.db`; it is persistent local storage, not a PostgreSQL database. The
database file is ignored by git. Set `DATABASE_ENGINE=postgres` to require
PostgreSQL and receive an error instead of silently switching engines.

## Roles and administration

New registrations always receive the `shopper` role. After creating an account,
an operator can provision an administrator directly in PostgreSQL:

```sql
UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';
```

Replace the sample email with the account's normalized email. Admin endpoints
read the current role from the database on every request, so the change takes
effect without reissuing the token. Do not accept a role from the client.
Avoid promoting an account unless it is controlled by the shop administrator.

## API

- `POST /auth/register` accepts `{ "name", "email", "password" }` and returns
  `{ "success", "message" }`.
- `POST /auth/login` accepts `{ "email", "password" }` and returns
  `{ "success", "message", "token", "user": { "name", "email", "role" } }`.
- Send `Authorization: Bearer <token>` to authenticated routes.
- `GET /products?skip=0&limit=100` remains public and paginated. Authenticated
  `POST /products` remains available to signed-in users.
- `GET /orders` returns the current user's orders with their stored item
  snapshots. `POST /orders` accepts `items` (`product_id`, `quantity`) plus
  `full_name`, `phone`, `address`, `city`, `state`, `pincode`, and
  `payment_method`. The server derives user/email from authentication and
  calculates the total from locked, current product rows; submitted totals or
  email fields are ignored.
- Admin-only routes: `GET/POST /admin/products`,
  `PUT/DELETE /admin/products/{id}`, `GET /admin/orders`, and
  `PATCH /admin/orders/{id}/status` (status: `pending`, `processing`,
  `shipped`, `delivered`, or `cancelled`).

Deleting a product referenced by an order is rejected to preserve order history.
