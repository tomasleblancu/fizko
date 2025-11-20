import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable cacheComponents to allow dynamic route segments
  cacheComponents: false,
};

export default nextConfig;
