FROM node:20-alpine

RUN npm install -g paperclipai

COPY entrypoint.sh /usr/local/bin/paperclip-entrypoint
RUN chmod +x /usr/local/bin/paperclip-entrypoint

WORKDIR /app
EXPOSE 3100
