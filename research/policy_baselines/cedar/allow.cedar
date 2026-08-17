@id("veriweave-publication-allow")
permit(
    principal,
    action,
    resource
)
when {
    !context.prohibited &&
    !(context.external && context.protectedData) &&
    !context.highImpact &&
    !context.unknownAction &&
    context.evidenceComplete
};
