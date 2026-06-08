"""Database package containing connection setup and table CRUD repositories."""

from database.connection import BaseRepository, init_all_tables

__all__ = ["BaseRepository", "init_all_tables"]
