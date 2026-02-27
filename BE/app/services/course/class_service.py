from app.core.logger import get_logger
from typing import List, Optional

from app.schemas.course import ClassCreateRequest, ClassResponse
from app.services.supabase.class_repository import ClassRepository
from app.services.supabase.document_repository import DocumentRepository

logger = get_logger(__name__)


class ClassService:
  def __init__(self, repo: ClassRepository, doc_repo: Optional[DocumentRepository] = None):
    self.repo = repo
    self.doc_repo = doc_repo

  async def list_classes(self, tenant_id: str, semester_id: Optional[str] = None, course_id: Optional[str] = None, access_token: str = None) -> List[ClassResponse]:
    raw_list = await self.repo.list_classes(
      tenant_id, semester_id, course_id, access_token)
    # Enrich with names from joins if present
    results = []
    for item in raw_list:
      course = item.get('courses') or {}
      semester = item.get('semesters') or {}

      # Map flat fields
      item['course_name'] = course.get('name')
      item['course_code'] = course.get('code')
      item['semester_name'] = semester.get('name')

      results.append(ClassResponse(**item))
    return results

  async def get_class(self, class_id: str, tenant_id: str, access_token: str = None) -> Optional[ClassResponse]:
    item = await self.repo.get_class(class_id, tenant_id, access_token)
    if item:
      course = item.get('courses') or {}
      semester = item.get('semesters') or {}

      item['course_name'] = course.get('name')
      item['course_code'] = course.get('code')
      item['semester_name'] = semester.get('name')

      return ClassResponse(**item)
    return None

  async def create_class(self, data: ClassCreateRequest, tenant_id: str, access_token: str = None) -> Optional[ClassResponse]:
    result = await self.repo.create_class(data, tenant_id, access_token)
    if result:
        # Basic return
      return ClassResponse(**result)
    return None

  async def enroll_student(self, class_id: str, user_id: str, tenant_id: str, access_token: str = None):
    return await self.repo.enroll_student(class_id, user_id, tenant_id, access_token)

  async def get_my_classes(self, user_id: str, tenant_id: str, access_token: str) -> List[ClassResponse]:
    # 1. Get Enrollments (Student)
    enrollments = await self.repo.get_student_enrollments(
      user_id, tenant_id, access_token)

    # 2. Get Instructor Assignments
    instructor_classes = await self.repo.get_classes_by_instructor(
      user_id, tenant_id, access_token)

    combined_classes = {}

    # Process Enrollments
    for enroll in enrollments:
      cls = enroll.get('classes')
      if cls:
        cls_id = cls.get('id')
        # Flatten joins
        course = cls.get('courses') or {}
        semester = cls.get('semesters') or {}

        cls['course_name'] = course.get('name')
        cls['course_code'] = course.get('code')
        cls['semester_name'] = semester.get('name')

        combined_classes[cls_id] = cls

    # Process Instructor Classes
    for cls in instructor_classes:
      cls_id = cls.get('id')
      if cls_id not in combined_classes:
        course = cls.get('courses') or {}
        semester = cls.get('semesters') or {}

        cls['course_name'] = course.get('name')
        cls['course_code'] = course.get('code')
        cls['semester_name'] = semester.get('name')

        combined_classes[cls_id] = cls

    return [ClassResponse(**c) for c in combined_classes.values()]

  async def get_class_students(self, class_id: str, tenant_id: str, access_token: str = None) -> List[dict]:
    data = await self.repo.get_class_students(class_id, tenant_id, access_token)
    # Flatten users
    students = []
    for item in data:
      user = item.get('users')
      if user:
        students.append({
            "enrollment_id": item.get('id'),
            "enrolled_at": item.get('enrolled_at'),
            "user_id": user.get('id'),
            "name": user.get('name'),
            "email": user.get('email')
        })
    return students

  async def get_dashboard_stats(self, tenant_id: str, access_token: str = None) -> dict:
    return await self.repo.get_stats(tenant_id, access_token)

  async def add_students_to_class(self, class_id: str, user_ids: List[str], tenant_id: str, access_token: str = None):
    # Depending on how the repository handles batch, we might loop or do batch insert
    # For now assuming repo has a method for this
    return await self.repo.add_students_to_class(class_id, user_ids, tenant_id, access_token)

  async def get_class_bots(self, class_id: str, tenant_id: str, access_token: str = None) -> List[dict]:
    bots = await self.repo.get_class_bots(class_id, tenant_id, access_token)
    # Bots are returned with joins, need to flatten if necessary or just return list
    return bots

  async def add_bots_to_class(self, class_id: str, bot_ids: List[str], tenant_id: str, access_token: str = None):
    return await self.repo.add_bots_to_class(class_id, bot_ids, tenant_id, access_token)

  async def remove_student_from_class(self, class_id: str, user_id: str, tenant_id: str, access_token: str = None):
    return await self.repo.remove_student_from_class(class_id, user_id, tenant_id, access_token)

  async def get_my_class_bots(self, user_id: str, tenant_id: str, access_token: str) -> List[dict]:
    classes = await self.get_my_classes(user_id, tenant_id, access_token)

    # Collect all unique bot IDs
    all_bot_ids = set()
    for cls in classes:
      if cls.bot_ids:
        for bid in cls.bot_ids:
          all_bot_ids.add(str(bid))

    if not all_bot_ids:
      return []

    # Fetch details for all unique bots in one go
    return await self.repo.get_bots_by_ids(list(all_bot_ids), access_token)

  async def remove_bot_from_class(self, class_id: str, bot_id: str, tenant_id: str, access_token: str = None):
    return await self.repo.remove_bot_from_class(class_id, bot_id, tenant_id, access_token)

  async def get_class_documents(self, class_id: str, tenant_id: str, access_token: str = None) -> List[dict]:
    # 1. Get Class Details (to get course_id)
    cls_data = await self.repo.get_class(class_id, tenant_id, access_token)
    if not cls_data:
      return []

    course_id = cls_data.get('course_id')
    if not course_id:
      return []

    # 2. Get Course Details (to get kb_ids)
    # We might need a course_repository or just use the joined data if get_class returns it
    # get_class select uses courses(*), so cls_data['courses'] should be there
    courses = cls_data.get('courses') or {}
    kb_ids = courses.get('kb_ids', [])

    if not kb_ids or not self.doc_repo:
      return []

    # 3. Aggregate all documents from those KBs
    all_docs = []
    seen_ids = set()

    for kb_id in kb_ids:
      docs = await self.doc_repo.get_documents_by_kb(
        str(kb_id), tenant_id, access_token)
      for doc in docs:
        if doc['id'] not in seen_ids:
          all_docs.append(doc)
          seen_ids.add(doc['id'])

    return all_docs

  async def get_class_kbs(self, class_id: str, tenant_id: str, access_token: str = None) -> List[dict]:
    """Retrieve metadata for all Knowledge Bases linked to this class's course."""
    # 1. Get Class -> Course -> kb_ids
    cls_data = await self.repo.get_class(class_id, tenant_id, access_token)
    if not cls_data:
      return []

    course = cls_data.get('courses') or {}
    kb_ids = course.get('kb_ids', [])

    if not kb_ids:
      return []

    from app.core.factory import get_knowledge_base_repository
    kb_repo = get_knowledge_base_repository()

    # Reuse get_retrieval_configs_by_ids which returns a dict {id: details}
    kb_map = await kb_repo.get_retrieval_configs_by_ids(
        [str(k) for k in kb_ids], tenant_id, access_token)

    # We want a list
    return list(kb_map.values())
