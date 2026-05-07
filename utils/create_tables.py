from utils import sqlite as db
from typing import Final


class Birthdays(db.Table):
    """
    Database table for storing user birthday information.
    """

    __tablename__: Final[str] = "birthdays"

    user_id = db.Column(
        "BIGINT",
        primary_key=True,
        nullable=False,
    )

    birthday = db.Column(
        "TIMESTAMP",
        nullable=False,
    )

    has_role = db.Column(
        "BOOLEAN",
        nullable=False,
        default=False,
    )


def creation(debug: bool = False) -> bool:
    """
    Create all registered database tables.

    Args:
        debug (bool):
            If True, prints successful table creation logs.

    Returns:
        bool:
            True if all tables were created successfully,
            otherwise False.
    """

    failed_tables = []

    for table in db.Table.all_tables():
        try:
            table.create()

            if debug:
                print(
                    f"[{table.__module__}] "
                    f"Created table: {table.__tablename__}"
                )

        except Exception as error:
            failed_tables.append(table.__tablename__)

            print(
                f"Failed to create table "
                f"'{table.__tablename__}'\n"
                f"Error: {error}\n"
            )

    if failed_tables:
        print(
            "Database initialization completed with errors.\n"
            f"Failed tables: {', '.join(failed_tables)}"
        )
        return False

    if debug:
        print("All database tables created successfully.")

    return True
