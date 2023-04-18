import psycopg as pg
from typing import Optional, List, Tuple, Dict


def delete_query(db: str,
                 schema_table: str,
                 where: Optional[dict] = None) -> Optional[str]:
    error = None
    sql = f"DELETE FROM {schema_table}"
    where_values = []
    if where is not None and len(where) > 0:
        sql = f"{sql} where "
        fields = list(where.keys())
        for idx in range(len(fields)):
            field = fields[idx]
            if idx == 0:
                and_operator = ''
            else:
                and_operator = 'AND'
            if isinstance(where[field], list):
                sql = f"{sql} {and_operator} {field} ("
                for value_idx in range(len(where[field])):
                    value = where[field][value_idx]
                    if value_idx == 0:
                        sql = f"{sql} %s"
                    else:
                        sql = f"{sql}, %s"
                    where_values.append(value)
                sql = f"{sql})"
            else:
                sql = f"{sql} {and_operator} {field}%s"
                where_values.append(where[field])

    try:

        with pg.connect(db) as conn:
            if len(where_values) > 0:
                conn.execute(sql, tuple(where_values))
            else:
                conn.execute(sql)

    except Exception as e:
        error = f"{e}"
    return error


def select_query(db: str,
                 schema_table: str,
                 where: Optional[dict] = None,
                 order_by: Optional[list] = None,
                 ascending: Optional[bool] = None) -> Tuple[List[dict], Optional[str]]:

    error = None
    records = []
    sql = f"SELECT * FROM {schema_table}"
    where_values = []
    if where is not None and len(where) > 0:
        sql = f"{sql} where "
        fields = list(where.keys())
        for idx in range(len(fields)):
            field = fields[idx]
            if idx == 0:
                and_operator = ''
            else:
                and_operator = 'AND'
            if isinstance(where[field], list):
                sql = f"{sql} {and_operator} {field} ("
                for value_idx in range(len(where[field])):
                    value = where[field][value_idx]
                    if value_idx == 0:
                        sql = f"{sql} %s"
                    else:
                        sql = f"{sql}, %s"
                    where_values.append(value)
                sql = f"{sql})"
            else:
                sql = f"{sql} {and_operator} {field}%s"
                where_values.append(where[field])

    if order_by is not None and len(order_by) > 0:
        sql = f"{sql} order by "
        for idx in range(len(order_by)):
            field = order_by[idx]
            if idx == 0:
                sql = f"{sql} {field}"
            else:
                sql = f"{sql}, {field}"

        if ascending is not None:
            if ascending:
                sql = f"{sql} ASC"
            else:
                sql = f"{sql} DESC"

    try:

        with pg.connect(db) as conn:
            if len(where_values) > 0:
                crsr = conn.execute(sql, tuple(where_values))
            else:
                crsr = conn.execute(sql)

            rows = crsr.fetchall()
            meta = crsr.description
            for row in rows:
                record = {meta[col_idx][0]: row[col_idx] for col_idx in range(len(meta))}
                records.append(record)

    except Exception as e:
        error = f"{e}"
    return records, error


def create_symbol_encoder_table(db: str) -> Optional[str]:
    error = None
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS samdb.symbol_encoder (
                                                encoder_id SERIAL PRIMARY KEY,
                                                encoder_name TEXT NOT NULL,
                                                dimension INT NOT NULL,
                                                max_nbits INT NOT NULL
                                                );
        """
        with pg.connect(db) as conn:
            conn.execute(sql)
    except Exception as e:
        error = f"{e}"
    return error


def select_symbol_encoder(db: str,
                          where: Optional[dict] = None,
                          order_by: Optional[list] = None,
                          ascending: Optional[bool] = None) -> Tuple[List[dict], Optional[str]]:
    records, error = select_query(db=db,
                                  schema_table='samdb.symbol_encoder',
                                  where=where,
                                  order_by=order_by,
                                  ascending=ascending)
    return records, error


def insert_symbol_encoder(db: str,
                          encoder_name: str,
                          dimension: int,
                          max_nbits: int) -> Tuple[Optional[dict], Optional[str]]:

    record = None
    sql = "INSERT INTO samdb.symbol_encoder (encoder_name, dimension, max_nbits) VALUES(%s, %s, %s)"
    params = (encoder_name, dimension, max_nbits)
    try:
        with pg.connect(db) as conn:
            conn.execute(sql, params)
        records, error = select_symbol_encoder(db=db, where={'encoder_name=': encoder_name})
        if len(records) > 0:
            record = records[0]
    except Exception as e:
        error = f"{e}"

    return record, error


def create_symbol_to_bits_table(db: str) -> Optional[str]:
    error = None
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS samdb.symbol_to_bits (
                                                map_id SERIAL PRIMARY KEY,
                                                encoder_id INT NOT NULL,
                                                symbol_int INT,
                                                symbol_str TEXT,
                                                bit INT NOT NULL
                                                );
        """
        with pg.connect(db) as conn:
            conn.execute(sql)
    except Exception as e:
        error = f"{e}"
    return error


def insert_symbol_to_bits(db: str,
                          encoder_id: int,
                          bits: List[int],
                          symbol_int: Optional[int] = None,
                          symbol_str: Optional[str] = None,
                          ) -> Optional[str]:

    # prepare rows to insert
    #
    rows_to_insert = [(encoder_id, symbol_int, symbol_str, bit) for bit in bits]

    error = None
    try:
        with pg.connect(db) as conn:
            with conn.cursor() as cur:
                with cur.copy("COPY samdb.symbol_to_bits (encoder_id, symbol_int, symbol_str, bit) FROM STDIN") as copy:
                    for row in rows_to_insert:
                        copy.write_row(row)

    except Exception as e:
        error = f"{e}"
    return error


def select_symbol_to_bits(db: str,
                          encoder_name: str) -> Tuple[List[dict], Optional[str]]:
    error = None
    records = []
    try:
        sql = """SELECT t1.* FROM samdb.symbol_to_bits t1, samdb.symbol_encoder t2 
                WHERE t1.encoder_id = t2.encoder_id AND
                        t2.encoder_name = %s;
              """
        with pg.connect(db) as conn:
            crsr = conn.execute(sql, (encoder_name, ))

            rows = crsr.fetchall()
            meta = crsr.description
            for row in rows:
                record = {meta[col_idx][0]: row[col_idx] for col_idx in range(len(meta))}
                records.append(record)

    except Exception as e:
        error = f"{e}"
    return records, error


def create_numeric_encoder_table(db: str) -> Optional[str]:
    error = None
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS samdb.numeric_encoder (
                                                encoder_id SERIAL PRIMARY KEY,
                                                encoder_name TEXT NOT NULL,
                                                dimension INT NOT NULL,
                                                max_nbits INT NOT NULL,
                                                q_step REAL NOT NULL,
                                                lower_bit_index INT NOT NULL,
                                                lower_q_value REAL NOT NULL,
                                                upper_bit_index INT NOT NULL,
                                                upper_q_value REAL NOT NULL
                                                );
        """
        with pg.connect(db) as conn:
            conn.execute(sql)
    except Exception as e:
        error = f"{e}"
    return error


def select_numeric_encoder(db: str,
                           where: Optional[dict] = None,
                           order_by: Optional[list] = None,
                           ascending: Optional[bool] = None) -> Tuple[List[dict], Optional[str]]:
    records, error = select_query(db=db,
                                  schema_table='samdb.numeric_encoder',
                                  where=where,
                                  order_by=order_by,
                                  ascending=ascending)
    return records, error


def insert_numeric_encoder(db: str,
                           encoder_name: str,
                           dimension: int,
                           max_nbits: int,
                           q_step: float,
                           lower_bit_index: int,
                           lower_q_value: float,
                           upper_bit_index: int,
                           upper_q_value: float
                           ) -> Tuple[Optional[dict], Optional[str]]:

    record = None
    sql = "INSERT INTO samdb.numeric_encoder (encoder_name, dimension, max_nbits, q_step, lower_bit_index, lower_q_value, upper_bit_index, upper_q_value) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
    params = (encoder_name, dimension, max_nbits, q_step,lower_bit_index, lower_q_value, upper_bit_index, upper_q_value)
    try:
        with pg.connect(db) as conn:
            conn.execute(sql, params)
        records, error = select_symbol_encoder(db=db, where={'encoder_name=': encoder_name})
        if len(records) > 0:
            record = records[0]
    except Exception as e:
        error = f"{e}"

    return record, error


def create_numeric_to_bits_table(db: str) -> Optional[str]:
    error = None
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS samdb.numeric_to_bits (
                                                map_id SERIAL PRIMARY KEY,
                                                encoder_id INT NOT NULL,
                                                numeric_int INT,
                                                numeric_float REAL,
                                                bit INT NOT NULL
                                                );
        """
        with pg.connect(db) as conn:
            conn.execute(sql)
    except Exception as e:
        error = f"{e}"
    return error


def insert_numeric_to_bits(db: str,
                           encoder_id: int,
                           bits: List[int],
                           numeric_int: Optional[int] = None,
                           numeric_float: Optional[float] = None,
                          ) -> Optional[str]:
    # prepare rows to insert
    #
    rows_to_insert = [(encoder_id, numeric_int, numeric_float, bit) for bit in bits]

    error = None
    try:
        with pg.connect(db) as conn:
            with conn.cursor() as cur:
                with cur.copy("COPY samdb.numeric_to_bits (encoder_id, numeric_int, numeric_str, bit) FROM STDIN") as copy:
                    for row in rows_to_insert:
                        copy.write_row(row)

    except Exception as e:
        error = f"{e}"
    return error


def select_numeric_to_bits(db: str,
                           encoder_name: str) -> Tuple[List[dict], Optional[str]]:
    error = None
    records = []
    try:
        sql = """SELECT t1.* FROM samdb.numeric_to_bits t1, samdb.numeric_encoder t2 
                WHERE t1.encoder_id = t2.encoder_id AND
                        t2.encoder_name = %s;
              """
        with pg.connect(db) as conn:
            crsr = conn.execute(sql, (encoder_name, ))

            rows = crsr.fetchall()
            meta = crsr.description
            for row in rows:
                record = {meta[col_idx][0]: row[col_idx] for col_idx in range(len(meta))}
                records.append(record)

    except Exception as e:
        error = f"{e}"
    return records, error


def configure_new_db(db: str) -> Tuple[List[str], Optional[str]]:
    error = None
    tables_added = []
    db_schema = {'samdb': {'symbol_encoder': create_symbol_encoder_table,
                           'symbol_to_bits': create_symbol_to_bits_table,
                           'numeric_encoder': create_numeric_encoder_table,
                           'numeric_to_bits': create_numeric_to_bits_table}}

    try:
        with pg.connect(db) as conn:
            for schema in db_schema:
                conn.execute(f"create schema if not exists {schema}")

            for schema in db_schema:
                crsr = conn.execute("select table_name from information_schema.tables where table_schema=%s", (schema,))

                existing_tables = {row[0] for row in crsr.fetchall()}
                tables_to_add = set(db_schema[schema].keys()) - existing_tables
                for table in tables_to_add:
                    error = db_schema[schema][table](db=db)
                    if error is not None:
                        break
                    else:
                        tables_added.append(table)
    except Exception as e:
        error = f"{e}"

    return tables_added, error


if __name__ == '__main__':

    host = 'localhost'
    port = 5432
    dbname = 'samdb'
    user = 'samdb_user'
    password = 'samdb123'

    db = f"host={host} port={port} dbname={dbname} user={user} password={password}"

    tables_added, error = configure_new_db(db=db)

    insert_symbol_encoder()
    pass
