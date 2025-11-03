/** @type {import('next').NextConfig} */
const nextConfig = {
  // basePath: '/cotizador', // Comentado para desarrollo local
  // assetPrefix: '/cotizador', // Comentado para desarrollo local
  output: "standalone",
  env: {
    // expose basePath to client automatically
    // NEXT_PUBLIC_BASE_PATH: '/cotizador', // Comentado para desarrollo local
  },
};

export default nextConfig;
