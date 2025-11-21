/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: '/cotizador',
  assetPrefix: '/cotizador',
  output: "standalone",
  env: {
    // expose basePath to client automatically
    NEXT_PUBLIC_BASE_PATH: '/cotizador',
  },
};

export default nextConfig;
