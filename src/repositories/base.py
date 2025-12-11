"""Base repository utilities.

This module contains a lightweight `BaseRepository` which stores a
SQLAlchemy `Session` instance. Application repositories inherit from
this class to reuse the session handling.
"""

from sqlalchemy.orm import Session


class BaseRepository:
    """Simple base class for repositories.

    Repositories should accept a SQLAlchemy `Session` instance and use
    it to perform database operations. This class only stores the
    session instance for subclasses to use.
    """

    def __init__(self, db: Session):
        """Initialize the repository with a DB session.

        Args:
            db: SQLAlchemy `Session` used for DB operations.
        """
        self.db = db
