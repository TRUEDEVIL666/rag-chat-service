from app.core.logger import get_logger
from typing import List, Optional
from app.schemas.course import (
  ClassCreateRequest,
  ClassResponse,
  CourseCreateRequest,
  CourseResponse,
  SemesterCreateRequest,
  SemesterResponse,
)
from app.repositories import (
  ClassRepository,
  CourseRepository,
  DocumentRepository,
  KnowledgeBaseRepository,
  SemesterRepository,
)

logger = get_logger(__name__)


class CourseService:
  _instance = None

  @classmethod
  def get_instance(cls) -> "CourseService":
    if cls._instance is None:
      from app.repositories import (
        ClassRepository,
        CourseRepository,
        DocumentRepository,
        KnowledgeBaseRepository,
        SemesterRepository,
      )

      cls._instance = cls(
        course_repo=CourseRepository.get_instance(),
        semester_repo=SemesterRepository.get_instance(),
        class_repo=ClassRepository.get_instance(),
        document_repo_instance=DocumentRepository.get_instance(),
        kb_repo=KnowledgeBaseRepository.get_instance(),
      )
    return cls._instance

  def __init__(
    self,
    course_repo: CourseRepository,
    semester_repo: SemesterRepository,
    class_repo: ClassRepository,
    document_repo_instance: Optional[DocumentRepository] = None,
    kb_repo: Optional[KnowledgeBaseRepository] = None,
  ):
    self.course_repo = course_repo
    self.semester_repo = semester_repo
    self.class_repo = class_repo
    self.document_repo_instance = document_repo_instance
    self.kb_repo = kb_repo

  # --- SEMESTERS ---
  async def list_semesters(self) -> List[SemesterResponse]:
    raw_list = await self.semester_repo.list_semesters()
    return [SemesterResponse(**item) for item in raw_list]

  async def create_semester(
    self, data: SemesterCreateRequest
  ) -> Optional[SemesterResponse]:
    result = await self.semester_repo.create_semester(data)
    if result:
      return SemesterResponse(**result)
    return None

  # --- COURSES ---
  async def list_courses(
    self, semester_id: Optional[str] = None
  ) -> List[CourseResponse]:
    raw_list = await self.course_repo.list_courses(semester_id)
    return [CourseResponse(**item) for item in raw_list]

  async def get_course(self, course_id: str) -> Optional[CourseResponse]:
    result = await self.course_repo.get_course(course_id)
    if result:
      return CourseResponse(**result)
    return None

  async def create_course(self, data: CourseCreateRequest) -> Optional[CourseResponse]:
    result = await self.course_repo.create_course(data)
    if result:
      return CourseResponse(**result)
    return None

  # --- CLASSES ---
  async def list_classes(
    self, semester_id: Optional[str] = None, course_id: Optional[str] = None
  ) -> List[ClassResponse]:
    raw_list = await self.class_repo.list_classes(semester_id, course_id)
    # Enrich with names from joins if present
    results = []
    for item in raw_list:
      course = item.get("courses") or {}
      semester = item.get("semesters") or {}

      # Map flat fields
      item["course_name"] = course.get("name")
      item["course_code"] = course.get("code")
      item["semester_name"] = semester.get("name")

      results.append(ClassResponse(**item))
    return results

  async def get_class(self, class_id: str) -> Optional[ClassResponse]:
    item = await self.class_repo.get_class(class_id)
    if item:
      course = item.get("courses") or {}
      semester = item.get("semesters") or {}

      item["course_name"] = course.get("name")
      item["course_code"] = course.get("code")
      item["semester_name"] = semester.get("name")

      return ClassResponse(**item)
    return None

  async def create_class(self, data: ClassCreateRequest) -> Optional[ClassResponse]:
    result = await self.class_repo.create_class(data)
    if result:
      # Basic return
      return ClassResponse(**result)
    return None

  async def enroll_student(self, class_id: str, user_id: str):
    return await self.class_repo.enroll_student(class_id, user_id)

  async def get_my_classes(self) -> List[ClassResponse]:
    from app.core.context import get_current_user_id

    user_id = get_current_user_id()
    # 1. Get Enrollments (Student)
    enrollments = await self.class_repo.get_student_enrollments(user_id)

    # 2. Get Instructor Assignments
    instructor_classes = await self.class_repo.get_classes_by_instructor(user_id)

    combined_classes = {}

    # Process Enrollments
    for enroll in enrollments:
      cls = enroll.get("classes")
      if cls:
        cls_id = cls.get("id")
        # Flatten joins
        course = cls.get("courses") or {}
        semester = cls.get("semesters") or {}

        cls["course_name"] = course.get("name")
        cls["course_code"] = course.get("code")
        cls["semester_name"] = semester.get("name")

        combined_classes[cls_id] = cls

    # Process Instructor Classes
    for cls in instructor_classes:
      cls_id = cls.get("id")
      if cls_id not in combined_classes:
        course = cls.get("courses") or {}
        semester = cls.get("semesters") or {}

        cls["course_name"] = course.get("name")
        cls["course_code"] = course.get("code")
        cls["semester_name"] = semester.get("name")

        combined_classes[cls_id] = cls

    return [ClassResponse(**c) for c in combined_classes.values()]

  async def get_class_students(self, class_id: str) -> List[dict]:
    data = await self.class_repo.get_class_students(class_id)
    # Flatten users
    students = []
    for item in data:
      user = item.get("users")
      if user:
        students.append(
          {
            "enrollment_id": item.get("id"),
            "enrolled_at": item.get("enrolled_at"),
            "user_id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
          }
        )
    return students

  async def get_dashboard_stats(self) -> dict:
    return await self.class_repo.get_stats()

  async def add_students_to_class(self, class_id: str, user_ids: List[str]):
    return await self.class_repo.add_students_to_class(class_id, user_ids)

  async def get_class_bots(self, class_id: str) -> List[dict]:
    bots = await self.class_repo.get_class_bots(class_id)
    return bots

  async def add_bots_to_class(self, class_id: str, bot_ids: List[str]):
    return await self.class_repo.add_bots_to_class(class_id, bot_ids)

  async def remove_student_from_class(self, class_id: str, user_id: str):
    return await self.class_repo.remove_student_from_class(class_id, user_id)

  async def get_my_class_bots(self) -> List[dict]:
    classes = await self.get_my_classes()

    # Collect all unique bot IDs
    all_bot_ids = set()
    for cls in classes:
      if cls.bot_ids:
        for bid in cls.bot_ids:
          all_bot_ids.add(str(bid))

    if not all_bot_ids:
      return []

    # Fetch details for all unique bots in one go
    return await self.class_repo.get_bots_by_ids(list(all_bot_ids))

  async def remove_bot_from_class(self, class_id: str, bot_id: str):
    return await self.class_repo.remove_bot_from_class(class_id, bot_id)

  async def get_class_documents(self, class_id: str) -> List[dict]:
    # 1. Get Class Details (to get course_id)
    cls_data = await self.class_repo.get_class(class_id)
    if not cls_data:
      return []

    course_id = cls_data.get("course_id")
    if not course_id:
      return []

    # 2. Get Course Details (to get kb_ids)
    courses = cls_data.get("courses") or {}
    kb_ids = courses.get("kb_ids", [])

    if not kb_ids or not self.document_repo_instance:
      return []

    # 3. Aggregate all documents from those KBs
    all_docs = []
    seen_ids = set()

    for kb_id in kb_ids:
      docs = await self.document_repo_instance.get_documents_by_kb(str(kb_id))
      for doc in docs:
        if doc["id"] not in seen_ids:
          all_docs.append(doc)
          seen_ids.add(doc["id"])

    return all_docs

  async def get_class_kbs(self, class_id: str) -> List[dict]:
    """Retrieve metadata for all Knowledge Bases linked to this class's course."""
    # 1. Get Class -> Course -> kb_ids
    cls_data = await self.class_repo.get_class(class_id)
    if not cls_data:
      return []

    course = cls_data.get("courses") or {}
    kb_ids = course.get("kb_ids", [])

    if not kb_ids:
      return []

    # Reuse get_retrieval_configs_by_ids which returns a dict {id: details}
    kb_map = await self.kb_repo.get_retrieval_configs_by_ids([str(k) for k in kb_ids])

    # We want a list
    return list(kb_map.values())
