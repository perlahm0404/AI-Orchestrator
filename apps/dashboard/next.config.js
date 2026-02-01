/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@ai-orchestrator/design-system'],

  // API proxy to Python backend
  async rewrites() {
    return [
      {
        source: '/api/orchestrator/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_APP_NAME: 'AI Orchestrator',
    NEXT_PUBLIC_API_URL: process.env.API_URL || 'http://localhost:8000',
  },
};

module.exports = nextConfig;
