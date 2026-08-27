from pydantic import BaseModel, EmailStr


class GoRequest(BaseModel):
    name: str
    email: EmailStr
