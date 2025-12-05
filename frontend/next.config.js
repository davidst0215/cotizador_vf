/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: '/cotizador',
  assetPrefix: '/cotizador',
  output: "standalone",
  env: {
    // expose basePath to client automatically
    NEXT_PUBLIC_BASE_PATH: '/cotizador',
  },
  // Force rebuild timestamp: 2025-12-04
};

export default nextConfig;
