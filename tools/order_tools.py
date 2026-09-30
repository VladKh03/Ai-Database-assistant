"""Validated order tools; SQL is formed by OrderRepository."""

from errors import error_info, MESSAGES
from api.schemas import (
    CreateOrderRequest, DeleteOrderRequest, GetCustomerOrdersRequest,
    GetOrderRequest, ToolResult, UpdateOrderRequest,
)
from database.repositories import OrderRepository
from tools._write_helper import write_result, read_result


def get_order(order_id: int, *, repository: OrderRepository | None = None) -> dict:
    try:
        request = GetOrderRequest.model_validate({"order_id": order_id})
        rows = (repository or OrderRepository()).get(request.order_id)
        return read_result(rows, required=True)
    except Exception as error:
        return ToolResult(success=False, **error_info(error)).model_dump(exclude_none=True)


def get_customer_orders(
    customer_id: str, *, repository: OrderRepository | None = None,
) -> dict:
    try:
        request = GetCustomerOrdersRequest.model_validate({"customer_id": customer_id})
        rows = (repository or OrderRepository()).get_customer_orders(request.customer_id)
        return ToolResult(success=True, rows=rows, row_count=len(rows)).model_dump(exclude_none=True)
    except Exception as error:
        return ToolResult(success=False, **error_info(error)).model_dump(exclude_none=True)


def create_order(*, repository: OrderRepository | None = None, **arguments) -> dict:
    repo = repository if repository is not None else OrderRepository()
    return write_result(CreateOrderRequest, repo.create, arguments)


def update_order(*, repository: OrderRepository | None = None, **arguments) -> dict:
    repo = repository if repository is not None else OrderRepository()

    def update(data: dict) -> dict:
        order_id = data.pop("order_id")
        return repo.update(order_id, data)

    return write_result(UpdateOrderRequest, update, arguments)


def delete_order(order_id: int, *, repository: OrderRepository | None = None) -> dict:
    repo = repository if repository is not None else OrderRepository()
    return write_result(
        DeleteOrderRequest,
        lambda data: repo.delete(data["order_id"]),
        {"order_id": order_id},
    )
