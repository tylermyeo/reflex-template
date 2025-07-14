from typing import Optional
from sqlmodel import Field, SQLModel, create_engine

class ProductPrice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    Product: str
    Region: str
    Region_Name: Optional[str] = Field(default=None)
    Currency: str
    Amount: float
    Period: str
    Page_Link: Optional[str] = Field(default=None)
    Timestamp: Optional[str] = Field(default=None)

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine) 