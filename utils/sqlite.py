import sqlite3

from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional


DATABASE_PATH = Path("storage.db")


def dict_factory(
    cursor: sqlite3.Cursor,
    row: tuple
) -> Dict[str, Any]:
    """
    Convert SQLite rows into dictionaries.
    """

    return {
        column[0]: row[index]
        for index, column in enumerate(cursor.description)
    }


class Database:
    """
    SQLite database helper class.
    """

    def __init__(
        self,
        database_path: Path = DATABASE_PATH
    ):
        self.conn = sqlite3.connect(
            database_path,
            isolation_level=None,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )

        self.conn.row_factory = dict_factory

        self.cursor = self.conn.cursor()

    def execute(
        self,
        sql: str,
        prepared: tuple = (),
    ) -> str:
        """
        Execute SQL query.

        Args:
            sql:
                SQL statement.

            prepared:
                Prepared statement values.

        Returns:
            str:
                Query execution status.
        """

        try:
            result = self.cursor.execute(
                sql,
                prepared,
            )

            statement = sql.strip().split()[0].upper()

            if statement == "SELECT":
                affected = len(result.fetchall())
            else:
                affected = max(result.rowcount, 0)

            return f"{statement} {affected}"

        except sqlite3.Error as error:
            return (
                f"{type(error).__name__}: "
                f"{error}"
            )

    def fetch(
        self,
        sql: str,
        prepared: tuple = (),
    ) -> List[Dict[str, Any]]:
        """
        Fetch all rows from query.
        """

        return self.cursor.execute(
            sql,
            prepared,
        ).fetchall()

    def fetchrow(
        self,
        sql: str,
        prepared: tuple = (),
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from query.
        """

        return self.cursor.execute(
            sql,
            prepared,
        ).fetchone()

    def close(self) -> None:
        """
        Close database connection.
        """

        self.cursor.close()
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ):
        self.close()


class Column:
    """
    Database column definition.
    """

    def __init__(
        self,
        column_type: str,
        *,
        primary_key: bool = False,
        index: bool = False,
        nullable: bool = True,
        unique: bool = False,
        name: Optional[str] = None,
        default: Any = None,
    ):
        self.column_type = column_type.upper()

        self.primary_key = primary_key
        self.index = index
        self.nullable = nullable
        self.unique = unique

        self.name = name
        self.default = default

        mutually_exclusive = (
            unique,
            primary_key,
            default is not None,
        )

        if sum(map(bool, mutually_exclusive)) > 1:
            raise SyntaxError(
                "'unique', 'primary_key', "
                "and 'default' are mutually exclusive."
            )

    def build(self) -> str:
        """
        Generate SQL column definition.
        """

        builder = [
            f"'{self.name}' {self.column_type}"
        ]

        if self.default is not None:
            builder.append("DEFAULT")

            if isinstance(self.default, str):
                builder.append(f"'{self.default}'")

            elif isinstance(self.default, bool):
                builder.append(
                    str(self.default).upper()
                )

            else:
                builder.append(str(self.default))

        elif self.unique:
            builder.append("UNIQUE")

        if not self.nullable:
            builder.append("NOT NULL")

        return " ".join(builder)


class TableMeta(type):
    """
    Metaclass for automatic column collection.
    """

    @classmethod
    def __prepare__(
        cls,
        name,
        bases,
        **kwargs
    ):
        return OrderedDict()

    def __new__(
        cls,
        name,
        bases,
        namespace,
        **kwargs
    ):
        table_name = kwargs.get(
            "table_name",
            name.lower(),
        )

        namespace["__tablename__"] = table_name

        columns = []

        for attribute, value in namespace.items():

            if isinstance(value, Column):

                if value.name is None:
                    value.name = attribute

                if value.index:
                    value.index_name = (
                        f"{table_name}_{value.name}_idx"
                    )

                columns.append(value)

        namespace["columns"] = columns

        return super().__new__(
            cls,
            name,
            bases,
            namespace,
        )


class Table(metaclass=TableMeta):
    """
    Base database table model.
    """

    @classmethod
    def create_table(
        cls,
        *,
        exists_ok: bool = True,
    ) -> str:
        """
        Generate CREATE TABLE SQL statement.
        """

        statements = []

        builder = ["CREATE TABLE"]

        if exists_ok:
            builder.append("IF NOT EXISTS")

        builder.append(cls.__tablename__)

        column_definitions = []
        primary_keys = []

        for column in cls.columns:

            column_definitions.append(
                column.build()
            )

            if column.primary_key:
                primary_keys.append(column.name)

        if primary_keys:
            column_definitions.append(
                (
                    "PRIMARY KEY "
                    f"({', '.join(primary_keys)})"
                )
            )

        builder.append(
            f"({', '.join(column_definitions)})"
        )

        statements.append(
            " ".join(builder) + ";"
        )

        for column in cls.columns:

            if column.index:

                statements.append(
                    (
                        "CREATE INDEX IF NOT EXISTS "
                        f"{column.index_name} "
                        f"ON {cls.__tablename__} "
                        f"({column.name});"
                    )
                )

        return "\n".join(statements)

    @classmethod
    def create(
        cls,
        *,
        verbose: bool = False,
    ) -> bool:
        """
        Create table in database.
        """

        sql = cls.create_table()

        if verbose:
            print(sql)

        with Database() as database:
            result = database.execute(sql)

        return not result.startswith(
            "OperationalError"
        )

    @classmethod
    def all_tables(cls):
        """
        Return all registered table models.
        """

        return cls.__subclasses__()
