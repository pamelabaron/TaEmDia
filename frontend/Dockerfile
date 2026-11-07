# Compila a interface e serve os arquivos estáticos com Nginx.
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npx ng build --configuration production

FROM nginx:1.27-alpine
COPY --from=build /app/dist/taemdia-web/browser /usr/share/nginx/html
# Redireciona as rotas do Angular para o index.html (aplicação de página única).
RUN printf 'server {\n  listen 80;\n  root /usr/share/nginx/html;\n  location / {\n    try_files $uri $uri/ /index.html;\n  }\n}\n' > /etc/nginx/conf.d/default.conf
