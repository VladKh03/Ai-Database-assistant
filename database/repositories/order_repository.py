"""Order record writes."""

from database.repositories.write_repository import WriteRepository


class OrderRepository(WriteRepository):
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

    def create(self, data: dict) -> dict:
        return self._create(data)

    def update(self, order_id: int, changes: dict) -> dict:
        return self._update(order_id, changes)