const { getDefaultConfig } = require("expo/metro-config");

const config = getDefaultConfig(__dirname);

config.resolver.resolveRequest = (context, moduleName, platform) => {
  // App and hoisted icon imports must share one native SVG view registry.
  const origin = moduleName === "react-native-svg" ? { ...context, originModulePath: __filename } : context;
  return context.resolveRequest(origin, moduleName, platform);
};

module.exports = config;
