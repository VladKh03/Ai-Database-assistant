"""Validated product tools; SQL is formed by ProductRepository."""

from errors import error_info, MESSAGES
from api.schemas import (
    CreateProductRequest, DeleteProductRequest, GetProductRequest,
    SearchProductsRequest, ToolResult, UpdateProductRequest,
)
from database.repositories import ProductRepository
from tools._write_helper import write_result, read_result


def get_product(product_id: int, *, repository: ProductRepository | None = None) -> dict:
    try:
        request = GetProductRequest.model_validate({"product_id": product_id})
        rows = (repository or ProductRepository()).get(request.product_id)
        return read_result(rows, required=True)
    except Exception as error:
        return ToolResult(success=False, **error_info(error)).model_dump(exclude_none=True)


def search_products(
    name: str | None = None, category_id: int | None = None,
    exact_name: bool = False, *, repository: ProductRepository | None = None,
) -> dict:
    try:
        request = SearchProductsRequest.model_validate(
            {"name": name, "category_id": category_id, "exact_name": exact_name}
        )
        rows = (repository or ProductRepository()).search(**request.model_dump(exclude_none=True))
        return ToolResult(success=True, rows=rows, row_count=len(rows)).model_dump(exclude_none=True)
    except Exception as error:
        return ToolResult(success=False, **error_info(error)).model_dump(exclude_none=True)


def create_product(*, repository: ProductRepository | None = None, **arguments) -> dict:
    repo = repository if repository is not None else ProductRepository()
    return write_result(CreateProductRequest, repo.create, arguments)


def update_product(*, repository: ProductRepository | None = None, **arguments) -> dict:
    repo = repository if repository is not None else ProductRepository()

    def update(data: dict) -> dict:
        product_id = data.pop("product_id")
        return repo.update(product_id, data)

    return write_result(UpdateProductRequest, update, arguments)


def delete_product(product_id: int, *, repository: ProductRepository | None = None) -> dict:
    repo = repository if repository is not None else ProductRepository()
    return write_result(
        DeleteProductRequest,
        lambda data: repo.delete(data["product_id"]),
        {"product_id": product_id},
    )
