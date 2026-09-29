"""Validated product and order write tools; SQL is owned by repositories."""

from api.schemas import (
    CreateProductRequest, UpdateProductRequest,
    CreateOrderRequest, UpdateOrderRequest,
)
from database.repositories import ProductRepository, OrderRepository
from tools._write_helper import write_result


def create_product(*, repository: ProductRepository | None = None, **arguments) -> dict:
    repo = repository if repository is not None else ProductRepository()
    return write_result(CreateProductRequest, repo.create, arguments)


def update_product(*, repository: ProductRepository | None = None, **arguments) -> dict:
    repo = repository if repository is not None else ProductRepository()

    def update(data: dict) -> dict:
        product_id = data.pop("product_id")
        return repo.update(product_id, data)

    return write_result(UpdateProductRequest, update, arguments)


def create_order(*, repository: OrderRepository | None = None, **arguments) -> dict:
    repo = repository if repository is not None else OrderRepository()
    return write_result(CreateOrderRequest, repo.create, arguments)


def update_order(*, repository: OrderRepository | None = None, **arguments) -> dict:
    repo = repository if repository is not None else OrderRepository()

    def update(data: dict) -> dict:
        order_id = data.pop("order_id")
        return repo.update(order_id, data)

    return write_result(UpdateOrderRequest, update, arguments)