from pydantic import BaseModel

class PredictionRequest(BaseModel):
    id: int
    query: str

class PredictionResponse(BaseModel):
    id: int
    answer: int | str
    reasoning: str
    sources: list[str]