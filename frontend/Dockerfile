FROM node:22-alpine
WORKDIR /app
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
ARG RENEWCALC_BACKEND_URL=http://backend:8000
ENV RENEWCALC_BACKEND_URL=$RENEWCALC_BACKEND_URL
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start"]
