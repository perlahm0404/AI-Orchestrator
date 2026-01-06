"""
Application Adapters

Thin wrappers that connect AI Brain to target application repos.

Adapters provide:
- Project-specific configuration (paths, commands)
- Ralph invocation for that project
- AppContext for the governance engine

Adapters do NOT:
- Define policy (that's in ralph/policy/)
- Make governance decisions (that's Ralph's job)
- Store state (stateless, config-only)

Each target app has its own adapter:
- adapters/karematch/
- adapters/credentialmate/

See: v4-RALPH-GOVERNANCE-ENGINE.md Section "Application-Level Design"
"""
