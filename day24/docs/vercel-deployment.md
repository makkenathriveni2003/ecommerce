# Day 24 – Task 3: Vercel Frontend Deployment (React + Vite SPA)

This guide documents deploying the ShopZone frontend to Vercel, managing environment variables, coordinating CORS, and connecting Git.

---

## 1. Frontend Framework Analysis

- **Framework:** React 19 with Vite 8 and TypeScript
- **Routing:** Client-side routing with `react-router-dom` (HTML5 History Mode)
- **State Management:** Zustand (`cartStore`, `authStore`, `favoritesStore`, `notificationStore`)
- **API Client:** Fetch-based REST client in `frontend/src/services/apiClient.ts`
- **Build Output:** Static assets in `frontend/dist/`

> [!NOTE]
> Because this is a **React SPA powered by Vite** (not a Next.js SSR application), converting it to Next.js is completely unnecessary and adds overhead.
> Vercel natively supports Vite single-page applications with instant global edge caching and zero server costs.

---

## 2. Vercel Configuration (`frontend/vercel.json`)

Vercel requires rewriting all non-asset requests to `/index.html` so that client-side routes (`/products`, `/checkout`, `/admin`, `/favorites`) work smoothly when refreshed directly in the browser:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "cleanUrls": true,
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

---

## 3. Environment Variables on Vercel

In Vite, variables exposed to the client browser **must begin with the `VITE_` prefix**.

Configure these in the **Vercel Project Settings > Environment Variables**:

| Variable Name | Environment | Value Example | Description |
| :--- | :--- | :--- | :--- |
| `VITE_API_URL` | Production | `https://api.yourdomain.com` | Base URL for FastAPI REST endpoints |
| `VITE_WS_URL` | Production | `wss://api.yourdomain.com/ws` | Secure WebSocket endpoint for live chat |
| `VITE_SENTRY_DSN` | Production | `https://publicKey@o0.ingest.sentry.io/0` | Public client DSN for Sentry browser tracking |
| `VITE_API_URL` | Preview / Dev | `http://<EC2_ELASTIC_IP>` | Staging backend URL |
| `VITE_WS_URL` | Preview / Dev | `ws://<EC2_ELASTIC_IP>/ws` | Staging WebSocket URL |

> [!WARNING]
> **Never store backend secrets in Vercel environment variables!**
> Variables starting with `VITE_` are bundled directly into the compiled JavaScript files and are visible to anyone inspecting network requests in browser developer tools.
> Backend API keys (`GEMINI_API_KEY`, `POSTGRES_PASSWORD`, `JWT_SECRET_KEY`) must **only** reside on the EC2 instance in `.env`.

---

## 4. Connecting Git Repository to Vercel (Step-by-Step)

1. **Sign in to Vercel:** Go to [vercel.com](https://vercel.com) and sign in using your GitHub account.
2. **Import Project:** Click **Add New... > Project** and select your `shopzone` GitHub repository.
3. **Configure Project Settings:**
   - **Root Directory:** Edit from `./` to `frontend` (click **Edit** next to Root Directory and select the `frontend` folder).
   - **Framework Preset:** `Vite` (automatically detected).
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`
4. **Add Environment Variables:**
   - Add `VITE_API_URL` -> `https://api.yourdomain.com` (or your EC2 IP)
   - Add `VITE_WS_URL` -> `wss://api.yourdomain.com/ws` (or your EC2 IP)
   - Add `VITE_SENTRY_DSN` -> (optional)
5. **Deploy:** Click **Deploy**. Vercel will install dependencies, build the application, and provide a production URL (e.g. `https://shopzone.vercel.app`).

---

## 5. Coordinating CORS with EC2 Backend

Once Vercel assigns your domain (e.g., `https://shopzone-gamma.vercel.app`):

1. SSH into your EC2 instance.
2. Open your backend `.env`:
   ```bash
   nano ~/shopzone/.env
   ```
3. Update `FRONTEND_ORIGINS` to include your Vercel domain:
   ```ini
   FRONTEND_ORIGINS=https://shopzone-gamma.vercel.app,http://localhost:5173
   ```
4. Restart the backend container:
   ```bash
   docker compose -f day24/docker-compose.prod.yml restart backend
   ```
5. Test an API call from the Vercel site to ensure the browser allows the request without CORS errors.
