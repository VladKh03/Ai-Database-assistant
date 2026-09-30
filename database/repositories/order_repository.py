from sqlalchemy import text
from errors import InvalidForeignKeyError

from database.repositories.write_repository import WriteRepository


class OrderRepository(WriteRepository):
    """Keep order headers and order items together"""
    table = "Orders"
    primary_key = "order_id"
    fields = {
        "order_id": "OrderID", "customer_id": "CustomerID",
        "employee_id": "EmployeeID", "order_date": "OrderDate",
        "required_date": "RequiredDate", "shipped_date": "ShippedDate",
        "ship_via": "ShipVia", "freight": "Freight",
        "ship_name": "ShipName", "ship_address": "ShipAddress",
        "ship_city": "ShipCity", "ship_region": "ShipRegion",
        "ship_postal_code": "ShipPostalCode", "ship_country": "ShipCountry",
    }

    def get(self, order_id: int) -> list[dict]:
        """Return one order with its product items"""
        with self.engine.connect() as connection:
            order = connection.execute(
                text('SELECT * FROM "Orders" WHERE "OrderID" = :order_id'),
                {"order_id": order_id},
            ).mappings().first()
            if order is None:
                return []
            details = connection.execute(
                text(
                    'SELECT d."ProductID", p."ProductName", d."UnitPrice", '
                    'd."Quantity", d."Discount" FROM "Order Details" AS d '
                    'JOIN "Products" AS p ON p."ProductID" = d."ProductID" '
                    'WHERE d."OrderID" = :order_id ORDER BY d."ProductID"'
                ),
                {"order_id": order_id},
            ).mappings()
            return [{**dict(order), "items": [dict(row) for row in details]}]

    def get_customer_orders(self, customer_id: str) -> list[dict]:
        """Return up to 20 recent orders for one customer"""
        with self.engine.connect() as connection:
            orders = connection.execute(
                text(
                    'SELECT * FROM "Orders" WHERE "CustomerID" = :customer_id '
                    'ORDER BY "OrderDate" DESC, "OrderID" DESC LIMIT 20'
                ),
                {"customer_id": customer_id},
            ).mappings()
            return [dict(row) for row in orders]

    def create(self, data: dict) -> dict:
        """Save the order and all its items in one transaction"""
        values = data.copy()
        items = values.pop("items", None)
        values = self._values(values)
        columns = ", ".join(f'"{self.fields[name]}"' for name in values)
        placeholders = ", ".join(f":{name}" for name in values)
        order_insert = text(
            f'INSERT INTO "Orders" ({columns}) VALUES ({placeholders})'
        )
        detail_insert = text(
            'INSERT INTO "Order Details" '
            '("OrderID", "ProductID", "UnitPrice", "Quantity", "Discount") '
            'VALUES (:order_id, :product_id, :unit_price, :quantity, :discount)'
        )

        with self._transaction() as connection:
            order_result = connection.execute(order_insert, values)
            # Use the new order ID for each order item
            order_id = order_result.lastrowid
            used_products = set()
            for item in items or []:
                if "product_id" in item:
                    products = connection.execute(
                        text(
                            'SELECT "ProductID", "UnitPrice" FROM "Products" '
                            'WHERE "ProductID" = :product_id'
                        ),
                        {"product_id": item["product_id"]},
                    ).mappings().all()
                else:
                    products = connection.execute(
                        text(
                            'SELECT "ProductID", "UnitPrice" FROM "Products" '
                            'WHERE "ProductName" = :name COLLATE NOCASE LIMIT 2'
                        ),
                        {"name": item["product_name"]},
                    ).mappings().all()
                if not products:
                    raise InvalidForeignKeyError("Order item product does not exist")
                if len(products) > 1:
                    raise ValueError("Order item product has an ambiguous name")
                product = products[0]
                product_id = product["ProductID"]
                # A product can appear only once in this order
                if product_id in used_products:
                    raise ValueError("The same product cannot appear twice in one order")
                used_products.add(product_id)
                unit_price = item.get("unit_price")
                # Use the current product price when the user gives no price
                if unit_price is None:
                    unit_price = product["UnitPrice"]
                if unit_price is None:
                    raise ValueError("Product has no price; provide unit_price")
                connection.execute(detail_insert, {
                    "order_id": order_id,
                    "product_id": product_id,
                    "unit_price": unit_price,
                    "quantity": item["quantity"],
                    "discount": item.get("discount", 0),
                })
            return {"rowcount": order_result.rowcount, "record_id": order_id}

    def update(self, order_id: int, changes: dict) -> dict:
        return self._update(order_id, changes)

    def delete(self, order_id: int) -> dict:
        """Delete the order items and the order in one transaction"""
        with self._transaction() as connection:
            connection.execute(
                text('DELETE FROM "Order Details" WHERE "OrderID" = :order_id'),
                {"order_id": order_id},
            )
            result = connection.execute(
                text('DELETE FROM "Orders" WHERE "OrderID" = :order_id'),
                {"order_id": order_id},
            )
            return {"rowcount": result.rowcount, "record_id": order_id}
