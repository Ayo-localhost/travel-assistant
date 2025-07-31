FROM node:22-alpine

RUN apk update && apk upgrade

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

EXPOSE 8080

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "8080"]