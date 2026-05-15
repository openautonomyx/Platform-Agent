# Platform Agent UI - Dockerfile

FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY ui/package*.json ./

# Install
RUN npm install

# Copy app
COPY ui/ ./

# Build
RUN npm run build

# Expose
EXPOSE 3000

# Start
CMD ["npm", "run", "preview"]