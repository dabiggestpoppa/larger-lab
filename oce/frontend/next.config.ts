import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/command-center/:path*",
        destination: "http://localhost:8000/command-center/:path*",
      },
    ];
  },
};

export default nextConfig;
