// eslint-disable-next-line import/no-extraneous-dependencies, @typescript-eslint/no-var-requires
const webpack = require("webpack");

module.exports = function override(config, env) {
  // do stuff with the webpack config...

  // eslint-disable-next-line no-param-reassign
  config.resolve.fallback = {
    url: require.resolve("url"),
    assert: require.resolve("assert"),
    crypto: require.resolve("crypto-browserify"),
    http: require.resolve("stream-http"),
    https: require.resolve("https-browserify"),
    os: require.resolve("os-browserify/browser"),
    buffer: require.resolve("buffer"),
    stream: require.resolve("stream-browserify"),
  };
  config.plugins.push(
    new webpack.ProvidePlugin({
      process: "process/browser",
      Buffer: ["buffer", "Buffer"],
    })
  );
  // eslint-disable-next-line no-param-reassign
  config.ignoreWarnings = [/Failed to parse source map/];

  return config;
};
