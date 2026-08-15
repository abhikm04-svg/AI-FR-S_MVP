# Vite bakes VITE_* env vars in at build time, not runtime -- pass the
# backend's browser-reachable URL as a build arg (NOT a Docker-internal
# service name; the browser calls this directly, it can't resolve
# Docker-network DNS).
ARG VITE_API_BASE_URL=http://localhost:8000

FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
