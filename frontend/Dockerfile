# Development image for the Vite dev server. Production serving (static build
# behind a CDN or nginx) is set up in the deployment phase; this image exists
# so `docker compose up` brings the frontend up with hot reload, matching the
# Docker-first workflow used for the backend.
FROM node:22-alpine

WORKDIR /app

# Install dependencies first so this layer is cached until the manifest changes.
# `npm install` (not `npm ci`) so the platform-specific native binaries for
# Tailwind and Vite are resolved for this image's OS/arch, which a lock file
# generated on the host does not fully capture.
COPY package.json package-lock.json ./
RUN npm install

COPY . .

EXPOSE 5173

# --host makes the dev server listen on all interfaces so it is reachable from
# the host. Compose can override this command.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
