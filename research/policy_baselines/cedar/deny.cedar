@id("veriweave-publication-deny")
permit(
    principal,
    action,
    resource
)
when {
    context.prohibited ||
    (context.external && context.protectedData)
};
