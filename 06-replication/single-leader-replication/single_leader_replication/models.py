"""
models.py

Defines request and response models used by the HTTP API. 

These models validate incoming client requests and ensure the API has a 
well-defined contract. 
"""

from typing import Any
from pydantic import BaseModel

class SetRequest(BaseModel):
    """
    Request body for storing a key-value pair.
    """
    key: str
    value: Any
    
class ValueResponse(BaseModel):
    """
    Response returned when retrieving a value.
    """
    
    key: str
    value: Any
    
class LogEntry(BaseModel):
    """
    Single log entry representing a write operation.
    """
    index: int
    operation: str
    key: str
    value: Any