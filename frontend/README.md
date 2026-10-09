# Daylight shop

A responsive, type-safe React storefront built with TypeScript, Vite, React
Router, Zustand, and TanStack Query. It has a Vitest/React Testing Library
component suite with MSW API mocks and a Playwright end-to-end test.

## Run locally

From the project root, install and start the FastAPI server:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --reload
```

Run the first command only if the project virtual environment does not exist.

The backend stores products, registered users, and orders in PostgreSQL. If
`backend/.env` does not exist, copy `backend/.env.example` to create it;
otherwise preserve your existing file and update its settings. Set
`PGPASSWORD` locally to the
PostgreSQL password and replace `JWT_SECRET_KEY` with a random value of at
least 32 bytes. The default connection uses `localhost`, port `5432`, database
`sqlight`, and user `Thriveni`. On startup, the backend creates its tables but
does not add any products. Start the app, open **Add products**, create an
account or sign in, and submit the product form. The backend assigns each
product an ID and saves it in PostgreSQL. Products can also be added in
pgAdmin's Query Tool for the `sqlight` database:

```sql
INSERT INTO products (name, price, category, image)
VALUES ('Product name', 100.00, 'Category', 'https://example.com/image.jpg');
```

Product creation from the app requires signing in. New accounts can be created
from the same page.

## Checkout, orders, and administration

The storefront uses the PostgreSQL products table. Product cards link to a
database-backed product details page. The Zustand cart is shared across pages
and persists in browser local storage.

Sign in to check out. Checkout validates delivery information, then sends the
cart product IDs and quantities to FastAPI. The server must calculate the
authoritative price from PostgreSQL and save the order and order items in one
transaction; the browser clears the cart only after success. Order history is
loaded from the authenticated `GET /orders` API and is scoped to the signed-in
user.

New accounts have the `shopper` role. First start the backend once so it creates
or upgrades the schema, then register the account to promote. To grant it
administrator access, connect to `sqlight` as a trusted database administrator
and explicitly promote that user in pgAdmin's Query Tool:

```sql
UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';
```

Only users whose database role is `admin` can use `/admin` or the `/admin/*`
APIs. The dashboard supports product create, edit, delete, and order status
updates. Do not grant the admin role to untrusted accounts.

The login token is held in the current browser tab and expires. Sign in again
after expiration.

```dotenv
PGHOST=localhost
PGPORT=5432
PGDATABASE=sqlight
PGUSER=Thriveni
PGPASSWORD=your-local-postgresql-password
```

Keep `backend/.env` out of version control and never share its password.
Existing SQLite data is not migrated.

In another terminal, start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

The storefront requests product pages from `GET /products?skip=...&limit=...`.
The backend supports this pagination contract and permits the Vite development
and preview origins. The frontend uses `http://127.0.0.1:8000` by default. To configure it explicitly,
copy `.env.example` to `.env.local` and set `VITE_API_URL` to the backend base
URL, for example:

```dotenv
VITE_API_URL=http://127.0.0.1:8000
```

Restart the Vite server after changing `.env.local`.

## State and performance

- Zustand owns the cart and persists it in browser local storage. The auth
  store keeps the sign-in session for the current browser tab.
- The light/dark theme toggle saves the selected theme in browser local storage.
- TanStack Query manages product pages/details, checkout mutations, order
  history, and admin products/orders.
- Products displayed by the storefront are read from the PostgreSQL database.
- Cart, checkout, product detail, order history, and admin pages are
  lazy-loaded. Product cards are memoized and product images are lazy-loaded
  with responsive image parameters.

## Lighthouse

Run Lighthouse against the production build rather than Vite's development
server, which includes development-only tooling and can inflate JavaScript and
main-thread measurements:

```powershell
npm run build
npm run preview
```

Open `http://127.0.0.1:4173/` for the audit.

## Verify changes

Run these commands from `frontend`:

```powershell
npm run typecheck
npm run lint
npm test
npx playwright install chromium
npm run test:e2e
npm run build
```

Component tests use MSW and do not need a running FastAPI server. The Playwright
test also mocks the product API, so it exercises the storefront journey without
depending on a live backend. Run `npm test` for component/unit tests and
`npm run test:e2e` for the browser journey. These mocked tests do not replace a
live PostgreSQL integration check. GitHub Actions runs type checking, linting,
component tests, Playwright, and the production build on frontend changes.
