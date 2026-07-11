import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // This app lives in a subdir of the Python repo; pin the workspace root so
  // Turbopack stops warning about the parent project's files.
  turbopack: { root: __dirname },
};

export default nextConfig;
