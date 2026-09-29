"""Product record writes."""

from database.repositories.write_repository import WriteRepository


class ProductRepository(WriteRepository):
    table = "Products"
    primary_key = "product_id"
    fields = {
        "product_id": "ProductID", "product_name": "ProductName",
        "supplier_id": "SupplierID", "category_id": "CategoryID",
        "quantity_per_unit": "QuantityPerUnit", "unit_price": "UnitPrice",
        "units_in_stock": "UnitsInStock", "units_on_order": "UnitsOnOrder",
        "reorder_level": "ReorderLevel", "discontinued": "Discontinued",
    }

    def create(self, data: dict) -> dict:
        return self._create(self._normalize(data))

    def update(self, product_id: int, changes: dict) -> dict:
        return self._update(product_id, self._normalize(changes))

    @staticmethod
    def _normalize(data: dict) -> dict:
        values = data.copy()
        if "discontinued" in values and values["discontinued"] is not None:
            values["discontinued"] = str(int(values["discontinued"]))
        return values