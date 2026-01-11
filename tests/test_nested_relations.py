import unittest

from sqlalchemy import Column, ForeignKey, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.endpoints_logic.nested import NestedRelationConfig, apply_nested_relations


Base = declarative_base()


class Owner(Base):
    __tablename__ = "owners"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)


class Parent(Base):
    __tablename__ = "parents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("owners.id"), nullable=True)
    owner = relationship("Owner")
    children = relationship("Child", back_populates="parent")


class Child(Base):
    __tablename__ = "children"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    parent_id = Column(String, ForeignKey("parents.id"), nullable=True)
    parent = relationship("Parent", back_populates="children")


class TestNestedRelations(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        SessionLocal = sessionmaker(bind=self.engine)
        self.db = SessionLocal()

        self.relations = [
            NestedRelationConfig(
                name="owner",
                relation_type="belongs_to",
                target_model=Owner,
            ),
            NestedRelationConfig(
                name="children",
                relation_type="has_many",
                target_model=Child,
            ),
        ]

    def tearDown(self) -> None:
        self.db.close()

    def test_create_embedded_relations(self) -> None:
        parent = Parent(id="parent-1", name="Parent")
        payloads = {
            "owner": {"id": "owner-1", "name": "Owner"},
            "children": [
                {"id": "child-1", "name": "Child"},
            ],
        }

        apply_nested_relations(parent, payloads, self.relations, self.db, mode="create")
        self.db.add(parent)
        self.db.commit()

        self.assertIsNotNone(parent.owner)
        self.assertEqual(parent.owner.name, "Owner")
        self.assertEqual(len(parent.children), 1)
        self.assertEqual(parent.children[0].name, "Child")

    def test_update_appends_children(self) -> None:
        parent = Parent(id="parent-2", name="Parent")
        child = Child(id="child-2", name="Existing")
        parent.children.append(child)
        self.db.add(parent)
        self.db.commit()

        payloads = {
            "children": [
                {"id": "child-3", "name": "New"},
            ]
        }

        apply_nested_relations(parent, payloads, self.relations, self.db, mode="update")
        self.db.commit()

        self.assertEqual(len(parent.children), 2)

    def test_belongs_to_accepts_existing_id(self) -> None:
        owner = Owner(id="owner-2", name="Existing")
        parent = Parent(id="parent-3", name="Parent")
        self.db.add(owner)
        self.db.add(parent)
        self.db.commit()

        payloads = {"owner": "owner-2"}
        apply_nested_relations(parent, payloads, self.relations, self.db, mode="update")
        self.db.commit()

        self.assertEqual(parent.owner.id, "owner-2")
