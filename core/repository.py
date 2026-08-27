class BaseRepository:
    def __init__(self, table_name: str, pk_name: str, db):
        self._table = table_name
        self._pk = pk_name
        self._db = db

    def get_all(self, limit: int = 100, offset: int = 0):
        with self._db.cursor() as cursor:
            query = f"SELECT * FROM {self._table} LIMIT %s OFFSET %s;"
            cursor.execute(query, (limit, offset))
            return cursor.fetchall()

    def get_by_id(self, item_id: int):
        with self._db.cursor() as cursor:
            query = f"SELECT * FROM {self._table} WHERE {self._pk} = %s;"
            cursor.execute(query, (item_id,))
            return cursor.fetchone()

    def create(self, data: dict):
        keys = list(data.keys())
        values = list(data.values())
        columns = ", ".join(keys)
        placeholders = ", ".join(["%s"] * len(keys))
        query = f"INSERT INTO {self._table} ({columns}) VALUES ({placeholders}) RETURNING *;"
        
        with self._db.cursor() as cursor:
            cursor.execute(query, values)
            self._db.commit()
            return cursor.fetchone()

    def update(self, item_id: int, data: dict):
        if not data:
            return self.get_by_id(item_id)
        
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        values = list(data.values())
        values.append(item_id)
        query = f"UPDATE {self._table} SET {set_clause} WHERE {self._pk} = %s RETURNING *;"
        
        with self._db.cursor() as cursor:
            cursor.execute(query, values)
            self._db.commit()
            return cursor.fetchone()

    def delete(self, item_id: int):
        query = f"DELETE FROM {self._table} WHERE {self._pk} = %s;"
        with self._db.cursor() as cursor:
            cursor.execute(query, (item_id,))
            self._db.commit()
            return True