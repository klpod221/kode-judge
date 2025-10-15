from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.core.config import settings
from app.db.models import Submission, SubmissionStatus

# Tạo chuỗi kết nối ĐỒNG BỘ từ chuỗi bất đồng bộ
SYNC_DATABASE_URL = str(settings.DATABASE_URL).replace("+asyncpg", "")

engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def update_submission_status(db_session, submission_id: int, status: SubmissionStatus):
    stmt = (
        update(Submission)
        .where(Submission.id == submission_id)
        .values(status=status)
    )
    db_session.execute(stmt)
    db_session.commit()

def update_submission_result(db_session, submission_id: int, status: SubmissionStatus, stdout: str, stderr: str, meta: dict):
    stmt = (
        update(Submission)
        .where(Submission.id == submission_id)
        .values(
            status=status,
            stdout=stdout,
            stderr=stderr,
            meta=meta
        )
    )
    db_session.execute(stmt)
    db_session.commit()