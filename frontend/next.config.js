/** @type {import('next').NextConfig} */
const nextConfig = {
  ...(process.env.DOCKER_BUILD === "true" ? { output: "standalone" } : {}),
};

module.exports = nextConfig;
