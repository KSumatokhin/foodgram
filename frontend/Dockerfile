# build env
# FROM node:21.7.1-alpine
FROM node:22.9.0-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build
CMD cp -r build result_build
