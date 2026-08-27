from pydantic import BaseModel, EmailStr


class AddMemberRequest(BaseModel):
    email: EmailStr
