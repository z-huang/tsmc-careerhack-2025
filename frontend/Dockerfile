# Dockerfile
FROM nginx:alpine

# 複製你的網頁文件到 Nginx 的預設目錄
COPY index.html /usr/share/nginx/html/
COPY transcript.css /usr/share/nginx/html/
COPY transcript.js /usr/share/nginx/html/
COPY translations.json /usr/share/nginx/html/

# 設定 Nginx 設定檔（如果需要的話）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 設定容器的埠口
EXPOSE 8080