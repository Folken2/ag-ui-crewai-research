import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.BACKEND_URL 
          ? `${process.env.BACKEND_URL}/api/:path*`
          : 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
