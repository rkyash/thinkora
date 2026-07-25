# Build-only stage — validates the React app compiles successfully
# No nginx needed since this is for CI build checks only, not deployment
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build
