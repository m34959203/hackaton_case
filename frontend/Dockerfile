FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# NEXT_PUBLIC_ переменные встраиваются в клиентский JS при сборке.
# Для браузера API доступен через localhost:8000 (порт проброшен в docker-compose).
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# --- Production runner ---
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3100
ENV HOSTNAME=0.0.0.0

# Копируем standalone-сборку
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3100

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD wget -q --spider http://localhost:3100/ || exit 1

CMD ["node", "server.js"]
