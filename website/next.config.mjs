/** @type {import('next').NextConfig} */
const nextConfig = {
  // Emits .next/standalone with a pruned node_modules for a small runtime image.
  output: "standalone",
  experimental: {
    // The Mongo driver has optional native peers (kerberos, snappy, ...) that
    // webpack cannot resolve. Load it from node_modules at runtime instead.
    serverComponentsExternalPackages: ["mongodb"],
  },
};

export default nextConfig;
