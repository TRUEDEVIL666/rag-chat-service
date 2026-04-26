from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

# --------------------------
# SEMESTER
# --------------------------


class SemesterBase(BaseModel):
  name: str  # e.g. "Spring 2024"
  start_date: date
  end_date: date
  is_active: Optional[bool] = False


class SemesterCreateRequest(SemesterBase):
  pass


class SemesterResponse(SemesterBase):
  id: UUID
  tenant_id: UUID
  created_at: datetime

  class Config:
    from_attributes = True


# --------------------------
# COURSE (CATALOG)
# --------------------------


class CourseBase(BaseModel):
  code: str  # e.g. "IT001"
  name: str  # e.g. "Intro to Python"
  description: Optional[str] = None
  semester_id: UUID
  kb_ids: List[UUID] = []


class CourseCreateRequest(CourseBase):
  pass


class CourseResponse(CourseBase):
  id: UUID
  tenant_id: UUID
  created_at: datetime
  updated_at: datetime
  semester_name: Optional[str] = None

  class Config:
    from_attributes = True


# --------------------------
# CLASS (INSTANCE)
# --------------------------


class ClassBase(BaseModel):
  course_id: UUID
  semester_id: UUID
  name: str  # e.g. "Start Date Group"
  instructor_id: Optional[UUID] = None


class ClassCreateRequest(ClassBase):
  pass


class ClassResponse(ClassBase):
  id: UUID
  tenant_id: UUID
  created_at: datetime
  bot_ids: List[UUID] = []

  # Expanded info (optional)
  course_name: Optional[str] = None
  course_code: Optional[str] = None
  semester_name: Optional[str] = None

  class Config:
    from_attributes = True


# --------------------------
# ENROLLMENT & ASSIGNMENT
# --------------------------


class EnrollmentRequest(BaseModel):
  user_id: UUID
