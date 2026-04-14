from fastapi import APIRouter

from app.api.v1 import applications, auth, cicd, cost, deployments, evaluations, experiments, gateway, prompts

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
v1_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
v1_router.include_router(prompts.router, tags=["Prompts"])
v1_router.include_router(experiments.router, prefix="/experiments", tags=["Experiments"])
v1_router.include_router(evaluations.router, prefix="/eval", tags=["Evaluations"])
v1_router.include_router(cost.router, prefix="/cost", tags=["Cost & Analytics"])
v1_router.include_router(deployments.router, prefix="/deployments", tags=["Deployments"])
v1_router.include_router(gateway.router, prefix="/gateway", tags=["LLM Gateway"])
v1_router.include_router(cicd.router, prefix="/cicd", tags=["CI/CD"])
