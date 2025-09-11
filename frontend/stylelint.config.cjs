module.exports = {
  extends: "stylelint-config-standard",
  ignoreFiles: ["node_modules/**"],
  rules: {
    // e.g. turn off unknown at-rules if using Tailwind:
    "at-rule-no-unknown": [
      true,
      { ignoreAtRules: ["tailwind", "apply", "variants", "screen"] },
    ],
  },
};
