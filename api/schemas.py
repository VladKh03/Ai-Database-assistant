"""Validated request, response and tool payloads."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChatRequest(StrictSchema):
    message: str = Field(min_length=1)
    session_id: str | None = Field(default=None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_message(self):
        self.message = self.message.strip()
        if not self.message:
            raise ValueError("Message must not be empty")
        return self


class ChatResponse(StrictSchema):
    answer: str
    action: str | None = None
    session_id: str
    requires_confirmation: bool = False
    operation_id: str | None = None


class AgentFinish(StrictSchema):
    action: Literal["finish"]
    answer: str = Field(min_length=1)

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Answer must not be empty")
        return value


class ResetRequest(StrictSchema):
    session_id: str = Field(min_length=1, max_length=128)


class GetCustomerRequest(StrictSchema):
    customer_id: str = Field(min_length=1)

    @field_validator("customer_id")
    @classmethod
    def nonempty_customer_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Customer ID must not be empty")
        return value


class SearchCustomersRequest(StrictSchema):
    name: str | None = None
    country: str | None = None
    city: str | None = None

    @field_validator("name", "country", "city")
    @classmethod
    def nonempty_filter(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Search filters must not be empty")
        return value

    @model_validator(mode="after")
    def require_filter(self):
        if not any((self.name, self.country, self.city)):
            raise ValueError("Provide name, country, or city")
        return self


class GetProductRequest(StrictSchema):
    product_id: int = Field(gt=0)


class SearchProductsRequest(StrictSchema):
    name: str | None = None
    category_id: int | None = Field(default=None, gt=0)
    exact_name: bool = False

    @field_validator("name")
    @classmethod
    def nonempty_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Product name must not be empty")
        return value

    @model_validator(mode="after")
    def require_filter(self):
        if self.name is None and self.category_id is None:
            raise ValueError("Provide a name or category_id")
        if self.exact_name and self.name is None:
            raise ValueError("Exact name search requires a name")
        return self


class DeleteProductRequest(StrictSchema):
    product_id: int = Field(gt=0)


class UpdateCustomerRequest(StrictSchema):
    customer_id: str = Field(min_length=1)
    company_name: str | None = None
    contact_name: str | None = None
    contact_title: str | None = None
    address: str | None = None
    city: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None
    phone: str | None = None
    fax: str | None = None

    @field_validator("customer_id")
    @classmethod
    def nonempty_customer_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Customer ID must not be empty")
        return value

    @model_validator(mode="after")
    def require_change(self):
        if not (self.model_fields_set - {"customer_id"}):
            raise ValueError("Provide at least one customer field to update")
        return self


class ProductChanges(StrictSchema):
    product_name: str | None = Field(default=None, min_length=1)
    supplier_id: int | None = Field(default=None, gt=0)
    category_id: int | None = Field(default=None, gt=0)
    quantity_per_unit: str | None = None
    unit_price: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    units_in_stock: int | None = Field(default=None, ge=0)
    units_on_order: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    discontinued: bool | None = None

    @field_validator("product_name")
    @classmethod
    def valid_product_name(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("Product name must not be empty")
        return value.strip()


class UpdateProductRequest(ProductChanges):
    product_id: int = Field(gt=0)

    @model_validator(mode="after")
    def require_change(self):
        if not (self.model_fields_set - {"product_id"}):
            raise ValueError("Provide at least one product field to update")
        return self


class UpdateProductByNameRequest(ProductChanges):
    lookup_name: str = Field(min_length=1)

    @field_validator("lookup_name")
    @classmethod
    def nonempty_lookup_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Lookup name must not be empty")
        return value

    @model_validator(mode="after")
    def require_change(self):
        if not (self.model_fields_set - {"lookup_name"}):
            raise ValueError("Provide at least one product field to update")
        return self


class CreateCustomerRequest(StrictSchema):
    customer_id: str = Field(min_length=1)
    company_name: str = Field(min_length=1)
    contact_name: str | None = None
    contact_title: str | None = None
    address: str | None = None
    city: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None
    phone: str | None = None
    fax: str | None = None

    @field_validator("customer_id", "company_name")
    @classmethod
    def nonempty_required_field(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Required customer fields must not be empty")
        return value


class DeleteCustomerRequest(StrictSchema):
    customer_id: str = Field(min_length=1)

    @field_validator("customer_id")
    @classmethod
    def nonempty_customer_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Customer ID must not be empty")
        return value


class CreateProductRequest(StrictSchema):
    product_name: str = Field(min_length=1)
    supplier_id: int | None = Field(default=None, gt=0)
    category_id: int | None = Field(default=None, gt=0)
    quantity_per_unit: str | None = None
    unit_price: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    units_in_stock: int | None = Field(default=None, ge=0)
    units_on_order: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    discontinued: bool | None = None

    @field_validator("product_name")
    @classmethod
    def nonempty_product_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Product name must not be empty")
        return value


class OrderItemRequest(StrictSchema):
    product_id: int | None = Field(default=None, gt=0)
    product_name: str | None = Field(default=None, min_length=1)
    quantity: int = Field(gt=0)
    unit_price: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    discount: float = Field(default=0, ge=0, le=1, allow_inf_nan=False)

    @field_validator("product_name")
    @classmethod
    def nonempty_product_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Product name must not be empty")
        return value

    @model_validator(mode="after")
    def require_one_product_reference(self):
        if (self.product_id is None) == (self.product_name is None):
            raise ValueError("Provide exactly one of product_id or product_name")
        return self


class CreateOrderRequest(StrictSchema):
    customer_id: str = Field(min_length=1)
    employee_id: int | None = Field(default=None, gt=0)
    order_date: date | datetime | None = None
    required_date: date | datetime | None = None
    shipped_date: date | datetime | None = None
    ship_via: int | None = Field(default=None, gt=0)
    freight: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    ship_name: str | None = None
    ship_address: str | None = None
    ship_city: str | None = None
    ship_region: str | None = None
    ship_postal_code: str | None = None
    ship_country: str | None = None
    items: list[OrderItemRequest] | None = Field(default=None, min_length=1)

    @field_validator("customer_id")
    @classmethod
    def nonempty_customer_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Customer ID must not be empty")
        return value


class GetOrderRequest(StrictSchema):
    order_id: int = Field(gt=0)


class GetCustomerOrdersRequest(StrictSchema):
    customer_id: str = Field(min_length=1)

    @field_validator("customer_id")
    @classmethod
    def nonempty_customer_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Customer ID must not be empty")
        return value


class DeleteOrderRequest(StrictSchema):
    order_id: int = Field(gt=0)


class UpdateOrderRequest(StrictSchema):
    order_id: int = Field(gt=0)
    customer_id: str | None = None
    employee_id: int | None = Field(default=None, gt=0)
    order_date: date | datetime | None = None
    required_date: date | datetime | None = None
    shipped_date: date | datetime | None = None
    ship_via: int | None = Field(default=None, gt=0)
    freight: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    ship_name: str | None = None
    ship_address: str | None = None
    ship_city: str | None = None
    ship_region: str | None = None
    ship_postal_code: str | None = None
    ship_country: str | None = None

    @model_validator(mode="after")
    def require_change(self):
        if not (self.model_fields_set - {"order_id"}):
            raise ValueError("Provide at least one order field to update")
        return self


class ConfirmationRequest(StrictSchema):
    session_id: str = Field(min_length=1, max_length=128)
    operation_id: str = Field(min_length=1)
    confirmed: bool


WRITE_ARGUMENT_SCHEMAS = {
    "update_customer": UpdateCustomerRequest,
    "update_product": UpdateProductRequest,
    "create_customer": CreateCustomerRequest,
    "delete_customer": DeleteCustomerRequest,
    "create_product": CreateProductRequest,
    "delete_product": DeleteProductRequest,
    "create_order": CreateOrderRequest,
    "update_order": UpdateOrderRequest,
    "delete_order": DeleteOrderRequest,
}

READ_ARGUMENT_SCHEMAS = {
    "get_customer": GetCustomerRequest,
    "search_customers": SearchCustomersRequest,
    "get_product": GetProductRequest,
    "search_products": SearchProductsRequest,
    "get_order": GetOrderRequest,
    "get_customer_orders": GetCustomerOrdersRequest,
}


class ToolCall(StrictSchema):
    action: Literal[
        "query_database", "get_customer", "search_customers",
        "get_product", "search_products",
        "get_order", "get_customer_orders",
        "create_customer", "update_customer", "delete_customer",
        "create_product", "update_product", "delete_product",
        "create_order", "update_order", "delete_order",
    ]
    query: str | None = None
    arguments: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_action_payload(self):
        if self.action == "query_database":
            if self.query is None or not self.query.strip():
                raise ValueError("READ action requires a nonempty query")
            if "arguments" in self.model_fields_set:
                raise ValueError("READ action must not contain arguments")
            self.query = self.query.strip()
        elif self.action in READ_ARGUMENT_SCHEMAS:
            if "query" in self.model_fields_set:
                raise ValueError("Fixed READ action must not contain a query")
            if self.arguments is None:
                raise ValueError("Fixed READ action requires arguments")
            request = READ_ARGUMENT_SCHEMAS[self.action].model_validate(self.arguments)
            self.arguments = request.model_dump(exclude_none=True)
        else:
            if "query" in self.model_fields_set:
                raise ValueError("Write action must not contain a query")
            if self.arguments is None:
                raise ValueError("Write action requires arguments")
            schema = (
                UpdateProductByNameRequest
                if self.action == "update_product" and "lookup_name" in self.arguments
                else WRITE_ARGUMENT_SCHEMAS[self.action]
            )
            request = schema.model_validate(self.arguments)
            self.arguments = request.model_dump(exclude_unset=True)
        return self


class ToolResult(StrictSchema):
    success: bool
    rows: list[dict[str, Any]] | None = None
    row_count: int | None = Field(default=None, ge=0)
    rowcount: int | None = Field(default=None, ge=0)
    record_id: str | int | None = None
    error: str | None = None
