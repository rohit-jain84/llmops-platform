from enum import StrEnum


class ExperimentStatus(StrEnum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"


class DeploymentStatus(StrEnum):
    PENDING_EVAL = "pending_eval"
    EVAL_PASSED = "eval_passed"
    CANARY = "canary"
    ROLLED_OUT = "rolled_out"
    ROLLED_BACK = "rolled_back"


class EvalRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class HumanEvalCampaignStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"


class HumanEvalAssignmentStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
