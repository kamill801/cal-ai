const { withAndroidManifest } = require("expo/config-plugins");

module.exports = function withLegacyCameraStorage(config) {
  return withAndroidManifest(config, (mod) => {
    const permissions = mod.modResults.manifest["uses-permission"] ??= [];
    let storage = permissions.find((permission) => permission.$?.["android:name"] === "android.permission.WRITE_EXTERNAL_STORAGE");
    if (!storage) {
      storage = { $: { "android:name": "android.permission.WRITE_EXTERNAL_STORAGE" } };
      permissions.push(storage);
    }
    // SDK 54 ImagePicker requires storage permission only on Android API 24-28.
    storage.$["android:maxSdkVersion"] = "28";
    return mod;
  });
};
