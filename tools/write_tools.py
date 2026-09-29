"""Validated order write tools; SQL is owned by repositories."""

from api.schemas import (
    CreateOrderRequest, UpdateOrderRequest,
)
from database.repositories import OrderRepository
from tools._write_helper import write_result


def create_order(*, repository: OrderRepository | None = None, **arguments) -> dict:
    repo = repository if repository is not None else OrderRepository()
    return write_result(CreateOrderRequest, repo.create, arguments)


def update_order(*, repository: OrderRepository | None = None, **arguments) -> dict:
    repo = repository if repository is not None else OrderRepository()

    def update(data: dict) -> dict:
        order_id = data.pop("order_id")
        return repo.update(order_id, data)

    return write_result(UpdateOrderRequest, update, arguments)