import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/endpoints-editor",
        destination: "/endpoints/editor",
      },
    ];
  },
};

export default nextConfig;
