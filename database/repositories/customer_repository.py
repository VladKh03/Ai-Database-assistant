"""Customer record writes."""

from database.repositories.write_repository import WriteRepository


class CustomerRepository(WriteRepository):
    table = "Customers"
    primary_key = "customer_id"
    fields = {
        "customer_id": "CustomerID", "company_name": "CompanyName",
        "contact_name": "ContactName", "contact_title": "ContactTitle",
        "address": "Address", "city": "City", "region": "Region",
        "postal_code": "PostalCode", "country": "Country",
        "phone": "Phone", "fax": "Fax",
    }

    def create(self, data: dict) -> dict:
        return self._create(data)

    def update(self, customer_id: str, changes: dict) -> dict:
        return self._update(customer_id, changes)

    def delete(self, customer_id: str) -> dict:
        return self._delete(customer_id)