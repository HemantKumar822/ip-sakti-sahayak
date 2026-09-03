FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
EXPOSE 4173
