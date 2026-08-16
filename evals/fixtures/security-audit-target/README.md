# Fixture target for security-audit behavior checks

Not a real project. Used by `evals/test_behavior.py` to assert that the
security-audit skill would trigger on a Windows supply-chain audit request
and would inspect npm inventory, postinstall hooks, and env files without
printing secret values.
