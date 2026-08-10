# ---------------------------------------------------------------- builder
FROM node:22-alpine AS builder

WORKDIR /build

# Dependencies first — editing a component does not reinstall node_modules.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---------------------------------------------------------------- runtime
FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime

# The unprivileged image already runs as uid 101 and listens on 8080, so no
# root is needed and no chown dance on the cache directories.
COPY --from=builder /build/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
