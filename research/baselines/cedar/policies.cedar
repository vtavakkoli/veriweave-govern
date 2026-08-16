// Authorization-only Cedar reference baseline. Evidence and REVIEW semantics are
// measured by the surrounding benchmark rather than claimed as Cedar-native behavior.
permit(
  principal,
  action in [Action::"read", Action::"search", Action::"summarize", Action::"classify", Action::"draft"],
  resource
);

forbid(
  principal,
  action == Action::"send_external",
  resource
) when {
  context.data_classification == "secret" || context.data_classification == "restricted"
};
