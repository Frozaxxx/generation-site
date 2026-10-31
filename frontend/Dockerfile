# syntax=docker/dockerfile:1

# ────────────────────────────────────────────────
# Стадия 1 — сборка панели
# ────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

# ────────────────────────────────────────────────
# Стадия 2 — статика и прокси на backend
# ────────────────────────────────────────────────
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
