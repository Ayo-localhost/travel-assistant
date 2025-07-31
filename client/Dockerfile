# Use Node 20 (better for React 19)
FROM node:20-alpine


WORKDIR /app

# Copy package files first for better caching
COPY package.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Expose port
EXPOSE 3000


CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]