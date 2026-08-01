## Summary

Describe the problem and the change.

## Governance and security impact

- [ ] Policy behavior is unchanged, or the behavior change is documented.
- [ ] `deny > review > allow` precedence remains deterministic.
- [ ] Fail-safe handling remains intact.
- [ ] No secrets, personal data, customer data, or restricted material are included.
- [ ] Security-sensitive changes have been reviewed against `SECURITY.md`.

## Validation

- [ ] `ruff check app benchmark tests`
- [ ] `pytest -q`
- [ ] `python -m build`
- [ ] `python -m twine check dist/*`
- [ ] `make benchmark` when runtime behavior changed

## Compatibility and operations

Describe API, policy-schema, configuration, migration, deployment, and rollback
considerations.

## Documentation

- [ ] User-visible changes are documented.
- [ ] `CHANGELOG.md` is updated when applicable.
- [ ] Licensing implications have been reviewed.
