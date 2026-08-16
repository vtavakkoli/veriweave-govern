package veriweave

import rego.v1

default decision := "review"

decision := "deny" if {
  input.external == true
  input.data_classification in {"secret", "restricted"}
}

decision := "allow" if {
  input.action in {"read", "search", "summarize", "classify", "draft"}
  input.external == false
  input.impact in {"minimal", "low", "medium"}
}
