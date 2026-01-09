from .view_schemas import View

STORES_USER_COUNT_VIEW: View = View(
    name="stores_user_counts",
    query="""
        SELECT s.id,
               s.name,
               COUNT(us.id) AS user_count
        FROM stores AS s
        LEFT JOIN user_stores AS us ON us.store_id = s.id
            AND us.deleted_at IS NULL
        WHERE s.deleted_at IS NULL
        GROUP BY s.id, s.name;
    """,
)
