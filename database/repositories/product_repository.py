from sqlalchemy import text

from database.repositories.write_repository import WriteRepository


class ProductRepository(WriteRepository):
    """Read and change product records with fixed SQL fields"""
    table = "Products"
    primary_key = "product_id"
    fields = {
        "product_id": "ProductID", "product_name": "ProductName",
        "supplier_id": "SupplierID", "category_id": "CategoryID",
        "quantity_per_unit": "QuantityPerUnit", "unit_price": "UnitPrice",
        "units_in_stock": "UnitsInStock", "units_on_order": "UnitsOnOrder",
        "reorder_level": "ReorderLevel", "discontinued": "Discontinued",
    }

    def get(self, product_id: int) -> list[dict]:
        with self.engine.connect() as connection:
            result = connection.execute(
                text('SELECT * FROM "Products" WHERE "ProductID" = :product_id'),
                {"product_id": product_id},
            )
            return [dict(row) for row in result.mappings()]

    def search(
        self, name: str | None = None, category_id: int | None = None,
        exact_name: bool = False,
    ) -> list[dict]:
        """Find products by name or category"""
        clauses = []
        params = {}
        if name is not None:
            if exact_name:
                clauses.append('"ProductName" = :name COLLATE NOCASE')
                params["name"] = name
            else:
                escaped = name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                clauses.append('"ProductName" LIKE :name ESCAPE \'\\\'')
                params["name"] = f"%{escaped}%"
        if category_id is not None:
            clauses.append('"CategoryID" = :category_id')
            params["category_id"] = category_id
        if not clauses:
            raise ValueError("Provide a name or category_id")

        # Two matches are enough to show that a name is not unique
        limit = 2 if exact_name else 20
        statement = text(
            'SELECT * FROM "Products" WHERE ' + ' AND '.join(clauses)
            + f' ORDER BY "ProductName", "ProductID" LIMIT {limit}'
        )
        with self.engine.connect() as connection:
            result = connection.execute(statement, params)
            return [dict(row) for row in result.mappings()]

    def create(self, data: dict) -> dict:
        return self._create(self._normalize(data))

    def update(self, product_id: int, changes: dict) -> dict:
        return self._update(product_id, self._normalize(changes))

    def delete(self, product_id: int) -> dict:
        return self._delete(product_id)

    @staticmethod
    def _normalize(data: dict) -> dict:
        """Convert the discontinued value to the database format"""
        values = data.copy()
        if "discontinued" in values and values["discontinued"] is not None:
            values["discontinued"] = str(int(values["discontinued"]))
        return values