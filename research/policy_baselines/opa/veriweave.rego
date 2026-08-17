package veriweave

import rego.v1

default decision := "review"

protected_external if {
    input.external
    input.data_classification in {"secret", "restricted"}
}

decision := "deny" if {
    input.prohibited
}

decision := "deny" if {
    protected_external
}

decision := "allow" if {
    not input.prohibited
    not protected_external
    not input.high_impact
    not input.unknown_action
    input.evidence_complete
}
