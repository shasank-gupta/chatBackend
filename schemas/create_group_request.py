from pydantic import BaseModel


class CreateGroupRequest(BaseModel):
    name: str
