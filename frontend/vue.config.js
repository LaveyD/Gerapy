module.exports = {
  outputDir: "../backend/core/templates",
  assetsDir: "static",
  devServer: {
    host: "0.0.0.0",
    hot: true,
    proxy: {
      "/api/*": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  css: {
    sourceMap: true,
  },
};
