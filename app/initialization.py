from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Users, Roles, Permissions, RolePermissions, UserRoles, Stores
from app.auth.hashing import hash_string
from app.logging import child_logger

init_logger = child_logger.bind(module="initialization")


def create_admin_user(check_existing_users: bool, db: Session) -> None:
    """
    Creates an admin user with every permission if needed.
    """
    try:
        if check_existing_users:
            user_count = db.query(Users).count()
            if user_count > 0:
                init_logger.info("Users already exist. Skipping admin user creation.")
                return

        init_logger.info("Creating admin user...")

        existing_admins = db.query(Users).filter(
            Users.name == "admin",
            Users.email == "admin@admin.com"
        ).all()

        if existing_admins:
            init_logger.warning(f"Found {len(existing_admins)} admin user(s) with default credentials. Recreating...")
            for admin in existing_admins:
                db.query(UserRoles).filter(UserRoles.user_id == admin.id).delete(synchronize_session=False)
                db.delete(admin)
            db.flush()

        hashed_password = hash_string("admin")
        admin_user = Users(
            name="admin",
            password=hashed_password,
            email="admin@admin.com",
            cross_store_allowed=True
        )
        db.add(admin_user)
        db.flush()

        all_permissions = db.query(Permissions).all()
        if not all_permissions:
            init_logger.warning("No permissions found in DB. Consider running build_permissions first.")

        admin_role = db.query(Roles).filter(Roles.name == "admin").first()
        if not admin_role:
            admin_role = Roles(name="admin")
            db.add(admin_role)
            db.flush()

        role_permissions_links = []
        for perm in all_permissions:
            existing_link = db.query(RolePermissions).filter_by(role_id=admin_role.id, permission_id=perm.id).first()
            if not existing_link:
                role_permissions_links.append(
                    RolePermissions(role_id=admin_role.id, permission_id=perm.id)
                )

        if role_permissions_links:
            db.add_all(role_permissions_links)

        existing_user_role = db.query(UserRoles).filter_by(user_id=admin_user.id, role_id=admin_role.id).first()
        if not existing_user_role:
            user_role_link = UserRoles(user_id=admin_user.id, role_id=admin_role.id)
            db.add(user_role_link)

        db.commit()
        init_logger.info("Admin user and role created successfully.")

    except Exception as e:
        db.rollback()
        init_logger.error(f"Error during admin user creation: {e}")


def create_base_store(db: Session) -> None:
    """
    Creates a base store if no stores exist in the database.
    """
    try:
        store_count = db.query(Stores).count()
        if store_count > 0:
            init_logger.info("Stores already exist. Skipping base store creation.")
            return

        init_logger.info("Creating base store...")

        base_store = Stores(name="Base Store", address="Fake Address 1")
        db.add(base_store)
        db.commit()
        init_logger.info(f"Base store created successfully (id: {base_store.id})")

    except Exception as e:
        init_logger.error(f"Error while creating base store: {e}")
        db.rollback()


def initialize_database(check_existing_users: bool = True):
    """
    Initializes the database by creating an admin user and a sample store.
    """
    db: Session = next(get_db())
    try:
        create_admin_user(check_existing_users, db)
        create_base_store(db)
    finally:
        db.close()
