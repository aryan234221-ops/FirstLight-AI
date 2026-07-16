from pydantic import BaseModel
from typing import List

class Task(BaseModel):
    title: str
    description: str
    priority: str = "medium"


class Plan(BaseModel):
    goal: str
    tasks: List[Task]