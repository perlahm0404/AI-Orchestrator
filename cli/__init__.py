"""
AI Brain CLI

Command-line interface for human operators.

Commands:
    aibrain status              # Overall system status
    aibrain status TASK-123     # Specific task status
    aibrain approve TASK-123    # Approve fix, merge PR
    aibrain reject TASK-123     # Reject fix
    aibrain ko approve KO-001   # Approve Knowledge Object
    aibrain ko pending          # List pending KOs
    aibrain emergency-stop      # AI_BRAIN_MODE=OFF
    aibrain pause               # AI_BRAIN_MODE=PAUSED
    aibrain resume              # AI_BRAIN_MODE=NORMAL

See: v4-HITL-PROJECT-PLAN.md Section "CLI visibility"
"""
