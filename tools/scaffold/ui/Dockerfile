FROM node:20-alpine

WORKDIR /ui

COPY tools/scaffold/ui/package*.json /ui/
RUN npm install

COPY tools/scaffold/ui /ui

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0", "-p", "3000"]
