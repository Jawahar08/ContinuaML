import queue
import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any, Callable, Optional
from sqlmodel import Session, select
from app.db import engine
from app.models import Job, JobStatus, JobEvent, Log
from app.config import settings

logger = logging.getLogger("continuaml.queue")


class JobQueueManager:
    def __init__(self):
        self.in_memory_queue = queue.Queue()
        self.use_redis = False
        self.redis_client = None
        self.handlers: Dict[str, Callable[[str, Session], None]] = {}
        
        # Test Redis connectivity
        try:
            import redis
            self.redis_client = redis.from_url(settings.REDIS_URL, socket_timeout=1)
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Connected to Redis. Using Redis-backed job queue.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Falling back to In-Memory Queue.")
            self.use_redis = False

    def register_handler(self, job_type: str, handler: Callable[[str, Session], None]):
        self.handlers[job_type] = handler

    def enqueue(self, job_id: str, db: Session):
        """Enqueues a job into Redis or the in-memory fallback."""
        statement = select(Job).where(Job.id == job_id)
        job = db.exec(statement).first()
        if not job:
            raise ValueError(f"Job {job_id} not found in database")
            
        # Log transition to queued
        self.transition_job(job_id, JobStatus.QUEUED, db, "Job submitted")
        
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.rpush("continuaml:jobs", job_id)
            except Exception as e:
                logger.error(f"Redis rpush failed, using in-memory queue: {e}")
                self.in_memory_queue.put(job_id)
        else:
            self.in_memory_queue.put(job_id)

    def transition_job(self, job_id: str, to_status: JobStatus, db: Session, reason: str = None) -> Job:
        """Transitions job state and records a JobEvent log."""
        statement = select(Job).where(Job.id == job_id)
        job = db.exec(statement).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
            
        from_status = job.status
        job.status = to_status
        job.updated_at = datetime.utcnow()

        db.add(job)
        
        # Append event
        event = JobEvent(
            job_id=job_id,
            from_state=from_status.value,
            to_state=to_status.value,
            transition_reason=reason
        )
        db.add(event)
        db.commit()
        db.refresh(job)
        return job

    def write_log(self, job_id: str, content: str, level: str = "INFO"):
        with Session(engine) as db:
            log = Log(job_id=job_id, content=content, level=level)
            db.add(log)
            db.commit()

    def update_progress(self, job_id: str, progress: float, db: Session):
        statement = select(Job).where(Job.id == job_id)
        job = db.exec(statement).first()
        if job:
            job.progress = progress
            db.add(job)
            db.commit()

    def dequeue(self, timeout: float = 1.0) -> Optional[str]:
        """Dequeues a job ID from Redis or the in-memory fallback."""
        if self.use_redis and self.redis_client:
            try:
                # BLPOP returns (key, value)
                result = self.redis_client.blpop("continuaml:jobs", timeout=int(timeout))
                if result:
                    return result[1].decode("utf-8")
            except Exception as e:
                logger.error(f"Redis blpop failed, using in-memory: {e}")
        
        try:
            return self.in_memory_queue.get(timeout=timeout)
        except queue.Empty:
            return None

job_queue = JobQueueManager()
