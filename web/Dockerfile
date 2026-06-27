# web/Dockerfile
#
# Base image: node:20-slim (NOT node:20-alpine).
#
# Alpine's musl libc cannot load the @next/swc-linux-x64-gnu binary pinned
# in package-lock.json generated on macOS/Debian hosts. The alternate
# @next/swc-linux-x64-musl binary is absent from those lockfiles, so the
# Alpine build fails across team members. node:20-slim ships glibc and loads
# the swc binary correctly.
#
# Trade-off: image is ~640 MB vs the Lab's ~150 MB standalone target.
# This is intentional — do not "fix" this back to Alpine or standalone mode.
#
# NEXT_PUBLIC_API_URL is a build arg (not a runtime env var). Next.js bakes
# NEXT_PUBLIC_* values into the client bundle at BUILD time. Changing it
# after the image is built has no effect until the next rebuild.

FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/public        ./public
COPY --from=builder /app/.next         ./.next
COPY --from=builder /app/node_modules  ./node_modules
COPY --from=builder /app/package.json  ./package.json

EXPOSE 3000
CMD ["npm", "start"]