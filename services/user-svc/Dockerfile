FROM node:18-alpine

#create app directory
WORKDIR /app

#install dependencies
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

#create non-root user
RUN addgroup -g 1001 -S nodejs -u 1001

#copy app source
COPY --chown=nodejs:nodejs . .

#switch to non-root user
USER nodejs

#expose port
EXPOSE 3000

#healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
CMD node -e "require('http').get('http://localhost:3000/health', (res) => {process.exit(res.statusCode === 200 ? 0: 1) })"

#start the app
CMD ["npm", "start"]
