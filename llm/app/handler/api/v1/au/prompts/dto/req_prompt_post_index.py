from pydantic import Field, validator
from app.base.base_dto import BaseDto

class ReqPromptPostIndex(BaseDto):
    text: str = Field(description="text")