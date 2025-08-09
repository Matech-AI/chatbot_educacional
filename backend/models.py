from pydantic import BaseModel
from typing import Optional, List

class EducationalChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: str
    learning_path_id: Optional[str] = None
    is_learning_path_generative: bool = False
    course_name: Optional[str] = None
    learning_objectives: Optional[List[str]] = None