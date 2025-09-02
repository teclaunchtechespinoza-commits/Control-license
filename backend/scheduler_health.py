from fastapi import APIRouter
from apscheduler.schedulers.asyncio import AsyncIOScheduler

router = APIRouter()

def init_scheduler_health(scheduler: AsyncIOScheduler):
    @router.get("/scheduler/health")
    async def scheduler_health():
        jobs = scheduler.get_jobs()
        return {
            "job_count": len(jobs),
            "jobs": [j.id for j in jobs],
            "running": scheduler.running
        }
