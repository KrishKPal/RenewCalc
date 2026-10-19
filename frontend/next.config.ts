import type { NextConfig } from "next";

const backend = (process.env.RENEWCALC_BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const nextConfig: NextConfig = {
  async rewrites() {
    // Same-origin browser API: Next.js forwards to FastAPI server-side.
    return [{source: "/api/v1/:path*", destination: `${backend}/api/v1/:path*`}];
  },
};

export default nextConfig;
