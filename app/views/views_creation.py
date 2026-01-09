from app.database.database import engine
from sqlalchemy import text, inspect
from .view_queries import TENANTS_USER_COUNT_VIEW
from .view_schemas import View
from typing import List

default_views: List[View] = [
    TENANTS_USER_COUNT_VIEW,
]

def create_or_replace_view(view:View):
    resulting_query = f"CREATE VIEW {view.name} AS {view.query}"
    with engine.connect() as conn:
        inspector = inspect(conn)
        if inspector.has_table(view.name):
            conn.execute(text(f"DROP VIEW {view.name}"))

        conn.execute(text(resulting_query))
        conn.commit()

def create_default_views():
    for view in default_views:
        create_or_replace_view(view)
