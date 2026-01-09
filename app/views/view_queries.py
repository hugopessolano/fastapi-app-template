from .view_schemas import View

TENANTS_USER_COUNT_VIEW: View = View(
    name="tenants_user_counts",
    query="""
        SELECT s.id,
               s.name,
               COUNT(us.id) AS user_count
        FROM tenants AS s
        LEFT JOIN user_tenants AS us ON us.tenant_id = s.id
            AND us.deleted_at IS NULL
        WHERE s.deleted_at IS NULL
        GROUP BY s.id, s.name;
    """,
)
