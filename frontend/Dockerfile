# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build production bundle
COPY . .
RUN npm run build

# Production serve stage with Nginx
FROM nginx:alpine

# Copy built artifacts from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with reverse proxy for /api and WebSockets
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
