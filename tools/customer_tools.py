from errors import error_info
from api.schemas import (
    CreateCustomerRequest, DeleteCustomerRequest, GetCustomerRequest,
    SearchCustomersRequest, ToolResult, UpdateCustomerRequest,
)
from database.repositories import CustomerRepository
from tools._write_helper import write_result, read_result


def get_customer(customer_id: str, *, repository: CustomerRepository | None = None) -> dict:
    try:
        request = GetCustomerRequest.model_validate({"customer_id": customer_id})
        rows = (repository or CustomerRepository()).get(request.customer_id)
        return read_result(rows, required=True)
    except Exception as error:
        return ToolResult(success=False, **error_info(error)).model_dump(exclude_none=True)


def search_customers(
    name: str | None = None,
    country: str | None = None,
    city: str | None = None,
    *,
    repository: CustomerRepository | None = None,
) -> dict:
    try:
        request = SearchCustomersRequest.model_validate(
            {"name": name, "country": country, "city": city}
        )
        rows = (repository or CustomerRepository()).search(**request.model_dump(exclude_none=True))
        return ToolResult(success=True, rows=rows, row_count=len(rows)).model_dump(exclude_none=True)
    except Exception as error:
        return ToolResult(success=False, **error_info(error)).model_dump(exclude_none=True)


def create_customer(*, repository: CustomerRepository | None = None, **arguments) -> dict:
    repo = repository if repository is not None else CustomerRepository()
    return write_result(CreateCustomerRequest, repo.create, arguments)


def update_customer(*, repository: CustomerRepository | None = None, **arguments) -> dict:
    repo = repository if repository is not None else CustomerRepository()

    def update(data: dict) -> dict:
        customer_id = data.pop("customer_id")
        return repo.update(customer_id, data)

    return write_result(UpdateCustomerRequest, update, arguments)


def delete_customer(customer_id: str, *, repository: CustomerRepository | None = None) -> dict:
    repo = repository if repository is not None else CustomerRepository()
    return write_result(
        DeleteCustomerRequest,
        lambda data: repo.delete(data["customer_id"]),
        {"customer_id": customer_id},
    )
