# # Use Node 20 (better for React 19)
# FROM node:20-alpine


# WORKDIR /app

# # Copy package files first for better caching
# COPY package.json ./

# # Install dependencies
# RUN npm install

# # Copy source code
# COPY . .

# # Build the app
# RUN npm run build

# # Expose port
# EXPOSE 3000


# CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]

# Use Node 20 (better for React 19)
FROM node:20-alpine

WORKDIR /app

# Copy package files first for better caching
COPY client/package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy TypeScript config files
COPY client/tsconfig*.json ./
COPY client/vite.config.ts ./

# Copy source code
COPY client/. .

# Add this after COPY . .
RUN ls -la src/lib/
RUN cat tsconfig.app.json

# Build the app
RUN npm run build

# Expose port
EXPOSE 3000

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]