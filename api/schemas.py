"""Validated request, response and tool payloads."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import date, datetime

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


class UpdateProductRequest(StrictSchema):
    product_id: int = Field(gt=0)
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

    @model_validator(mode="after")
    def require_change(self):
        if not (self.model_fields_set - {"product_id"}):
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

    @field_validator("customer_id")
    @classmethod
    def nonempty_customer_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Customer ID must not be empty")
        return value


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
    operation_id: str = Field(min_length=1)
    confirmed: bool


WRITE_ARGUMENT_SCHEMAS = {
    "update_customer": UpdateCustomerRequest,
    "update_product": UpdateProductRequest,
    "create_customer": CreateCustomerRequest,
    "delete_customer": DeleteCustomerRequest,
    "create_product": CreateProductRequest,
    "create_order": CreateOrderRequest,
    "update_order": UpdateOrderRequest,
}

READ_ARGUMENT_SCHEMAS = {
    "get_customer": GetCustomerRequest,
    "search_customers": SearchCustomersRequest,
}

class ToolCall(StrictSchema):
    action: Literal[
        "query_database", "get_customer", "search_customers",
        "create_customer", "update_customer", "delete_customer",
        "create_product", "update_product", "create_order", "update_order",
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
                raise ValueError("Customer READ action must not contain a query")
            if self.arguments is None:
                raise ValueError("Customer READ action requires arguments")
            request = READ_ARGUMENT_SCHEMAS[self.action].model_validate(self.arguments)
            self.arguments = request.model_dump(exclude_none=True)
        else:
            if "query" in self.model_fields_set:
                raise ValueError("Write action must not contain a query")
            if self.arguments is None:
                raise ValueError("Write action requires arguments")
            request = WRITE_ARGUMENT_SCHEMAS[self.action].model_validate(self.arguments)
            self.arguments = request.model_dump(exclude_unset=True)
        return self


class ToolResult(StrictSchema):
    success: bool
    rows: list[dict[str, Any]] | None = None
    row_count: int | None = Field(default=None, ge=0)
    rowcount: int | None = Field(default=None, ge=0)
    record_id: str | int | None = None
    error: str | None = None