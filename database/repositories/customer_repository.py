from sqlalchemy import text

from database.repositories.write_repository import WriteRepository


class CustomerRepository(WriteRepository):
    """Read and change customer records with fixed SQL fields"""
    table = "Customers"
    primary_key = "customer_id"
    fields = {
        "customer_id": "CustomerID", "company_name": "CompanyName",
        "contact_name": "ContactName", "contact_title": "ContactTitle",
        "address": "Address", "city": "City", "region": "Region",
        "postal_code": "PostalCode", "country": "Country",
        "phone": "Phone", "fax": "Fax",
    }

    def get(self, customer_id: str) -> list[dict]:
        with self.engine.connect() as connection:
            result = connection.execute(
                text('SELECT * FROM "Customers" WHERE "CustomerID" = :customer_id'),
                {"customer_id": customer_id},
            )
            return [dict(row) for row in result.mappings()]

    def search(
        self, name: str | None = None, country: str | None = None,
        city: str | None = None,
    ) -> list[dict]:
        """Find customers by name, country or city"""
        clauses = []
        params = {}
        if name is not None:
            # Treat % and _ as text instead of search patterns
            escaped = name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            clauses.append(
                '("CompanyName" LIKE :name ESCAPE \'\\\' '
                'OR "ContactName" LIKE :name ESCAPE \'\\\')'
            )
            params["name"] = f"%{escaped}%"
        if country is not None:
            clauses.append('"Country" = :country COLLATE NOCASE')
            params["country"] = country
        if city is not None:
            clauses.append('"City" = :city COLLATE NOCASE')
            params["city"] = city
        if not clauses:
            raise ValueError("Provide name, country, or city")

        statement = text(
            'SELECT * FROM "Customers" WHERE ' + ' AND '.join(clauses)
            + ' ORDER BY "CompanyName", "CustomerID" LIMIT 20'
        )
        with self.engine.connect() as connection:
            result = connection.execute(statement, params)
            return [dict(row) for row in result.mappings()]

    def create(self, data: dict) -> dict:
        return self._create(data)

    def update(self, customer_id: str, changes: dict) -> dict:
        return self._update(customer_id, changes)

    def delete(self, customer_id: str) -> dict:
        return self._delete(customer_id)