# Build stage — build context is ./client (see docker-compose.yml)
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# The only browser-exposed setting; defaults to /api in code if unset. Passed
# as a build arg so the compiled bundle can be pointed at a different API base
# without editing source. Everything else stays server-side (never bundled).
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx configuration (nginx.conf lives at the client/ context root)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
