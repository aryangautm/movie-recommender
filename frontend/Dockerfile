FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_API_URL

ENV VITE_API_URL=$VITE_API_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

RUN npm run build

FROM nginx:1.25-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

# Create a non-root user and group for Nginx to run as.
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
RUN chown -R appuser:appgroup /usr/share/nginx/html && chmod -R 755 /usr/share/nginx/html
RUN chown -R appuser:appgroup /var/cache/nginx && \
    chown -R appuser:appgroup /var/log/nginx && \
    chown -R appuser:appgroup /etc/nginx/conf.d
RUN touch /var/run/nginx.pid && \
    chown -R appuser:appgroup /var/run/nginx.pid

USER appuser

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]