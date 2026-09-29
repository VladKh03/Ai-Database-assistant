"""Validated write tools; SQL is owned by database repositories."""

from collections.abc import Callable

from pydantic import BaseModel

from api.schemas import (
    CreateCustomerRequest, UpdateCustomerRequest, DeleteCustomerRequest,
    CreateProductRequest, UpdateProductRequest,
    CreateOrderRequest, UpdateOrderRequest, ToolResult,
)
from database.repositories import (
    CustomerRepository, ProductRepository, OrderRepository,
)


def _write(
    model: type[BaseModel],
    operation: Callable[[dict], dict],
    arguments: dict
) -> dict:
    try:
        request = model.model_validate(arguments)
        result = operation(
            request.model_dump(exclude_unset=True, mode="json")
        )
        changed = result["rowcount"] > 0

        return ToolResult(
            success=changed,
            rowcount=result["rowcount"],
            record_id=result.get("record_id"),
            error=None if changed else "Record not found",
        ).model_dump(exclude_none=True)
    except Exception as error:
        return ToolResult(
            success=False,
            error=str(error)
        ).model_dump(exclude_none=True)


def create_customer(
    *,
    repository: CustomerRepository | None = None,
    **arguments
) -> dict:
    repo = repository if repository is not None else CustomerRepository()
    return _write(CreateCustomerRequest, repo.create, arguments)


def update_customer(
    *,
    repository: CustomerRepository | None = None,
    **arguments
) -> dict:
    repo = repository if repository is not None else CustomerRepository()

    def update(data: dict) -> dict:
        customer_id = data.pop("customer_id")
        return repo.update(customer_id, data)

    return _write(UpdateCustomerRequest, update, arguments)


def delete_customer(
    *,
    repository: CustomerRepository | None = None,
    **arguments
) -> dict:
    repo = repository if repository is not None else CustomerRepository()
    return _write(
        DeleteCustomerRequest,
        lambda data: repo.delete(data["customer_id"]),
        arguments,
    )


def create_product(
    *,
    repository: ProductRepository | None = None,
    **arguments
) -> dict:
    repo = repository if repository is not None else ProductRepository()
    return _write(CreateProductRequest, repo.create, arguments)


def update_product(
    *,
    repository: ProductRepository | None = None,
    **arguments
) -> dict:
    repo = repository if repository is not None else ProductRepository()

    def update(data: dict) -> dict:
        product_id = data.pop("product_id")
        return repo.update(product_id, data)

    return _write(UpdateProductRequest, update, arguments)


def create_order(
    *,
    repository: OrderRepository | None = None,
    **arguments
) -> dict:
    repo = repository if repository is not None else OrderRepository()
    return _write(CreateOrderRequest, repo.create, arguments)


def update_order(
    *,
    repository: OrderRepository | None = None,
    **arguments
) -> dict:
    repo = repository if repository is not None else OrderRepository()

    def update(data: dict) -> dict:
        order_id = data.pop("order_id")
        return repo.update(order_id, data)

    return _write(UpdateOrderRequest, update, arguments)