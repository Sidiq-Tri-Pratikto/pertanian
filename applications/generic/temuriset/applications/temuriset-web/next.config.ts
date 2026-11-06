import type { NextConfig } from 'next';

// Browsers only ever call this origin, so session cookies stay first-party and the API needs no CORS.
// Rewrites are fixed at build time; deployment (spec 037) decides how production reaches the API.
const apiUrl = process.env.API_URL ?? 'http://localhost:8020';

const config: NextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  // Next is always started from this folder; pinning the root stops it adopting lockfiles found further up.
  turbopack: { root: process.cwd() },
  poweredByHeader: false,
  logging: {
    incomingRequests: {
      ignore: [/^\/undangan\//, /^\/api\/v1\/invitations\//, /^\/api\/v1\/dev\/mailbox\/?(?:\?|$)/],
    },
  },
  async rewrites() {
    return [
      { source: '/api/v1/:path*', destination: `${apiUrl}/api/v1/:path*` },
      { source: '/health/:path*', destination: `${apiUrl}/health/:path*` },
    ];
  },
};

export default config;
