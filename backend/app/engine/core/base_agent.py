from abc import ABC, abstractmethod
from app.engine.core.task import Plan

class BaseAgent(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def plan(self, goal: str) -> Plan:
        pass