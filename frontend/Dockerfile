# --- build the React app ---
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Call the backend on the same origin (nginx proxies /api -> backend). No IP hardcoding.
ENV VITE_API_BASE_URL=/api
RUN npm run build

# --- serve with nginx + proxy /api to the backend ---
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
