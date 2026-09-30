# Build the SPA, then serve it with nginx, which also proxies /api, /media and Django admin to the backend.
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_ADMIN_PATH=suqilic-control
ENV VITE_ADMIN_PATH=$VITE_ADMIN_PATH
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
