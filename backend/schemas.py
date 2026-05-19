from pydantic import BaseModel, Field, field_validator


class EmailRequest(BaseModel):
    to: str = Field(min_length=3)
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)

    @field_validator("to")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address")
        return value


class EmailPreview(BaseModel):
    name: str
    email: str
    subject_line: str
    body: str
