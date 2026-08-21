from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

db = SQLAlchemy()


def migrate_schema():
    """Apply small, idempotent SQLite schema migrations required by the app.

    This project currently uses SQLite without Alembic. SQLAlchemy's
    ``create_all`` does not add missing columns to an existing table, so the
    migration is performed explicitly and preserves existing rows.
    """
    engine = db.engine
    inspector = inspect(engine)

    if 'detections' in inspector.get_table_names():
        columns = {col['name'] for col in inspector.get_columns('detections')}
        if 'source' not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE detections "
                        "ADD COLUMN source VARCHAR(20) DEFAULT 'USER_UPLOAD'"
                    )
                )
                # Rows created by the old seed script all point to the shared
                # conveyor sample image; preserve them as DEMO data rather
                # than presenting them as real user uploads.
                connection.execute(
                    text(
                        "UPDATE detections SET source = 'DEMO' "
                        "WHERE image_path = 'uploads/waste/conveyor_sample.png'"
                    )
                )
