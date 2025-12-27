from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ProductCategory(BaseModel):
    id: str
    code: str
    name: str

    model_config = {"from_attributes": True}


class ProductCategoryCreate(BaseModel):
    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)

    @field_validator("code", "name", mode="before")
    @classmethod
    def _strip(cls, value):
        return str(value).strip()


__all__ = ["ProductCategory", "ProductCategoryCreate"]
