from typing import Annotated

from fastapi import Depends

from app.services import (
  AnalyticsService,
  AuthService,
  BotService,
  ChatService,
  DocumentService,
  KnowledgeBaseService,
  QuizService,
  SessionService,
  TenantService,
  UserService,
)
from app.utils.auth import get_current_user

# Current User Dependency
CurrentUser = Annotated[dict, Depends(get_current_user)]

# Service Dependencies
AnalyticsServiceDep = Annotated[
  AnalyticsService, Depends(AnalyticsService.get_instance)
]
AuthServiceDep = Annotated[AuthService, Depends(AuthService.get_instance)]
BotServiceDep = Annotated[BotService, Depends(BotService.get_instance)]
ChatServiceDep = Annotated[ChatService, Depends(ChatService.get_instance)]
DocumentServiceDep = Annotated[DocumentService, Depends(DocumentService.get_instance)]
KnowledgeBaseServiceDep = Annotated[
  KnowledgeBaseService, Depends(KnowledgeBaseService.get_instance)
]
QuizServiceDep = Annotated[QuizService, Depends(QuizService.get_instance)]
SessionServiceDep = Annotated[SessionService, Depends(SessionService.get_instance)]
TenantServiceDep = Annotated[TenantService, Depends(TenantService.get_instance)]
UserServiceDep = Annotated[UserService, Depends(UserService.get_instance)]
