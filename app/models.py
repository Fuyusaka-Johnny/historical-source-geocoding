from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Person(StrictModel):
    name: str
    action: str = ""


class DayRecord(StrictModel):
    day: str = Field(description="保留原文纪日，不推测公历日期")
    weather: str = ""
    locations: list[str] = Field(default_factory=list)
    people: list[Person] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    original_text: str = Field(min_length=1, description="输入文本中的连续原文片段")
    keywords: list[str] = Field(default_factory=list)


class ExtractionResult(StrictModel):
    records: list[DayRecord]


class ExtractRequest(StrictModel):
    text: str = Field(min_length=1, max_length=30000)

    @field_validator("text")
    @classmethod
    def reject_blank(cls, value):
        if not value.strip():
            raise ValueError("请输入史料文本")
        return value
