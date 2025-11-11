from pydantic import BaseModel

class View(BaseModel):
    name:str
    query:str