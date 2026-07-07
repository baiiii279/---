"""Tests for the FormatTemplate model."""
from datetime import datetime

import pytest
from sqlalchemy import inspect


class TestFormatTemplateModel:
    """Verify FormatTemplate model definition and persistence."""

    def test_model_imports(self):
        """FormatTemplate can be imported from app.models."""
        from app.models import FormatTemplate
        assert FormatTemplate is not None

    def test_table_name(self):
        """FormatTemplate uses the correct table name."""
        from app.models.format_template import FormatTemplate

        assert FormatTemplate.__tablename__ == "format_templates"

    def test_columns_exist(self, db_session):
        """FormatTemplate has the expected columns with correct types."""
        from app.models.format_template import FormatTemplate

        inspector = inspect(db_session.bind)
        columns = {col["name"]: col for col in inspector.get_columns("format_templates")}

        assert "id" in columns
        assert columns["id"]["type"].__class__.__name__ == "INTEGER"
        assert not columns["id"].get("nullable", True)

        assert "user_id" in columns
        assert columns["user_id"]["type"].__class__.__name__ == "INTEGER"
        assert not columns["user_id"].get("nullable", True)

        assert "name" in columns
        assert columns["name"]["type"].__class__.__name__ in ("VARCHAR", "VARCHAR2")
        assert not columns["name"].get("nullable", True)

        assert "rules" in columns
        assert columns["rules"]["type"].__class__.__name__ in ("TEXT", "CLOB")
        assert not columns["rules"].get("nullable", True)

        assert "is_default" in columns
        assert columns["is_default"]["type"].__class__.__name__ in ("BOOLEAN", "INT", "INTEGER")

        assert "created_at" in columns

    def test_create_and_retrieve(self, db_session):
        """A FormatTemplate instance can be persisted and retrieved."""
        from app.models.format_template import FormatTemplate
        from app.models.user import User

        user = User(username="testuser", email="test@example.com", password_hash="hunter2")
        db_session.add(user)
        db_session.flush()

        template = FormatTemplate(
            user_id=user.id,
            name="学术论文格式",
            rules='{"font": "宋体", "size": 12}',
            is_default=True,
        )
        db_session.add(template)
        db_session.commit()

        saved = db_session.query(FormatTemplate).filter_by(name="学术论文格式").first()
        assert saved is not None
        assert saved.user_id == user.id
        assert saved.rules == '{"font": "宋体", "size": 12}'
        assert saved.is_default is True
        assert isinstance(saved.created_at, datetime)
