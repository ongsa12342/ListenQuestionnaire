# frontend/Dockerfile

# ---- Stage 1: Build React app ----
FROM node:14-alpine as build
WORKDIR /app

# Copy package.json and package-lock.json first (for better caching)
COPY package*.json ./
RUN npm install

# Copy the rest of the frontend source code
COPY . .

# Build React app for production
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
