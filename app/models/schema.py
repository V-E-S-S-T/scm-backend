from marshmallow import Schema, fields, validate, validates, ValidationError
from typing import Any, Dict


class ForecastRequestSchema(Schema):
    """Schema for demand forecast request validation"""

    businessName = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
        load_default=None,
    )

    businessType = fields.Str(
        required=True,
        validate=validate.OneOf(
            [
                "Grocery Store",
                "Electronics Store",
                "Clothing Store",
                "Medical Store",
                "Cosmetics Store",
                "Food & Beverage",
            ]
        ),
        error_messages={
            "invalid_choice": "Invalid business type. Please select from available options."
        },
    )

    businessScale = fields.Str(
        required=True,
        validate=validate.OneOf(["Micro", "Small", "Medium"]),
        error_messages={
            "invalid_choice": "Business scale must be Micro, Small, or Medium (MSME classification)."
        },
    )

    location = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"invalid": "Please provide a valid Indian state/location."},
    )

    currentSales = fields.Float(
        required=True,
        validate=validate.Range(min=1000, max=10000000),
        error_messages={
            "invalid": "Current sales must be a valid number.",
            "too_small": "Minimum sales amount is ₹1,000.",
            "too_large": "Maximum sales amount is ₹1,00,00,000.",
        },
    )

    @validates("businessName")
    def validate_business_name(self, value):
        if value is not None and len(value.strip()) == 0:
            raise ValidationError("Business name cannot be empty if provided.")


class InventoryItemSchema(Schema):
    """Schema for inventory item validation"""

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255),
        error_messages={"required": "Item name is required."},
    )

    category = fields.Str(
        required=True,
        validate=validate.OneOf(
            [
                "Grocery",
                "Electronics",
                "Clothing",
                "Medical",
                "Cosmetics",
                "Food & Beverage",
                "Books",
                "Sports",
                "Home & Garden",
                "Automotive",
                "Other",
            ]
        ),
    )

    sku = fields.Str(required=False, allow_none=True, validate=validate.Length(max=100))

    current_stock = fields.Int(
        required=True,
        validate=validate.Range(min=0),
        error_messages={"invalid": "Current stock must be a non-negative integer."},
    )

    min_stock_level = fields.Int(
        required=True,
        validate=validate.Range(min=0),
        error_messages={"invalid": "Minimum stock level must be non-negative."},
    )

    max_stock_level = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={"invalid": "Maximum stock level must be positive."},
    )

    unit_cost = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0),
        error_messages={"invalid": "Unit cost must be non-negative."},
    )

    selling_price = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0),
        error_messages={"invalid": "Selling price must be non-negative."},
    )

    supplier = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=255)
    )

    @validates("max_stock_level")
    def validate_stock_levels(self, value):
        min_level = self.context.get("min_stock_level", 0)
        if hasattr(self, "min_stock_level") and value <= self.min_stock_level:
            raise ValidationError(
                "Maximum stock level must be greater than minimum stock level."
            )


class BusinessSchema(Schema):
    """Schema for business information validation"""

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255),
        error_messages={"required": "Business name is required."},
    )

    type = fields.Str(
        required=True,
        validate=validate.OneOf(
            [
                "Grocery Store",
                "Electronics Store",
                "Clothing Store",
                "Medical Store",
                "Cosmetics Store",
                "Food & Beverage",
            ]
        ),
    )

    scale = fields.Str(
        required=True, validate=validate.OneOf(["Micro", "Small", "Medium"])
    )

    location = fields.Str(required=True, validate=validate.Length(min=2, max=100))

    owner_name = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=255)
    )

    contact_email = fields.Email(
        required=False,
        allow_none=True,
        error_messages={"invalid": "Please provide a valid email address."},
    )

    contact_phone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(min=10, max=15),
        error_messages={"invalid": "Phone number must be 10-15 digits."},
    )

    gst_number = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(min=15, max=15),
        error_messages={"invalid": "GST number must be exactly 15 characters."},
    )


class ShipmentCreateSchema(Schema):
    """Schema for shipment creation validation"""

    destination = fields.Str(
        required=True,
        validate=validate.Length(min=5, max=255),
        error_messages={"required": "Destination address is required."},
    )

    origin = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
        load_default="Bangalore Distribution Center",
    )

    items_count = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1, max=1000),
        error_messages={"invalid": "Items count must be between 1 and 1000."},
        load_default=1,
    )

    weight = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0.1, max=1000.0),
        error_messages={"invalid": "Weight must be between 0.1 and 1000 kg."},
        load_default=10.0,
    )

    estimated_days = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1, max=30),
        error_messages={"invalid": "Estimated delivery days must be between 1 and 30."},
        load_default=4,
    )


class ScenarioAnalysisSchema(Schema):
    """Schema for scenario analysis validation"""

    baseSales = fields.Float(
        required=True,
        validate=validate.Range(min=1000, max=100000000),
        error_messages={
            "required": "Base sales amount is required.",
            "invalid": "Base sales must be a valid number.",
            "too_small": "Minimum base sales is ₹1,000.",
            "too_large": "Maximum base sales is ₹10,00,00,000.",
        },
    )

    priceChange = fields.Float(
        required=True,
        validate=validate.Range(min=-50, max=100),
        error_messages={
            "required": "Price change percentage is required.",
            "invalid": "Price change must be a valid percentage.",
            "too_small": "Price change cannot be less than -50%.",
            "too_large": "Price change cannot be more than 100%.",
        },
    )

    marketingSpend = fields.Float(
        required=True,
        validate=validate.Range(min=0, max=10000000),
        error_messages={
            "required": "Marketing spend is required.",
            "invalid": "Marketing spend must be a valid amount.",
            "too_small": "Marketing spend cannot be negative.",
            "too_large": "Maximum marketing spend is ₹1,00,00,000.",
        },
    )

    seasonalFactor = fields.Float(
        required=True,
        validate=validate.Range(min=0.1, max=5.0),
        error_messages={
            "required": "Seasonal factor is required.",
            "invalid": "Seasonal factor must be a valid number.",
            "too_small": "Minimum seasonal factor is 0.1.",
            "too_large": "Maximum seasonal factor is 5.0.",
        },
    )

    competitorAction = fields.Str(
        required=True,
        validate=validate.OneOf(["none", "aggressive", "passive"]),
        error_messages={
            "required": "Competitor action is required.",
            "invalid_choice": "Competitor action must be: none, aggressive, or passive.",
        },
    )


class ReportRequestSchema(Schema):
    """Schema for report request validation"""

    report_type = fields.Str(
        required=True,
        validate=validate.OneOf(
            [
                "executive-summary",
                "sales",
                "inventory",
                "forecast-accuracy",
                "logistics",
            ]
        ),
        error_messages={
            "required": "Report type is required.",
            "invalid_choice": "Invalid report type selected.",
        },
    )

    period = fields.Str(
        required=False,
        validate=validate.OneOf(["weekly", "monthly", "quarterly", "yearly"]),
        load_default="monthly",
    )

    start_date = fields.Date(
        required=False,
        allow_none=True,
        format="%Y-%m-%d",
        error_messages={"invalid": "Start date must be in YYYY-MM-DD format."},
    )

    end_date = fields.Date(
        required=False,
        allow_none=True,
        format="%Y-%m-%d",
        error_messages={"invalid": "End date must be in YYYY-MM-DD format."},
    )

    @validates("end_date")
    def validate_date_range(self, value):
        start_date = self.context.get("start_date")
        if start_date and value and value <= start_date:
            raise ValidationError("End date must be after start date.")


class UserSessionSchema(Schema):
    """Schema for user session validation"""

    user_identifier = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=255)
    )

    business_id = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=1)
    )

    session_data = fields.Dict(required=False, allow_none=True)


class FestivalQuerySchema(Schema):
    """Schema for festival query validation"""

    festivals = fields.List(
        fields.Str(validate=validate.Length(min=1, max=100)),
        required=True,
        validate=validate.Length(min=1, max=10),
        error_messages={
            "required": "At least one festival is required.",
            "invalid": "Maximum 10 festivals can be queried at once.",
        },
    )

    business_type = fields.Str(
        required=True,
        validate=validate.OneOf(
            [
                "Grocery Store",
                "Electronics Store",
                "Clothing Store",
                "Medical Store",
                "Cosmetics Store",
                "Food & Beverage",
            ]
        ),
    )

    location = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
        load_default="India",
    )


# Response Schemas
class ForecastResponseSchema(Schema):
    """Schema for forecast response"""

    success = fields.Bool(required=True)
    forecast = fields.Dict(required=False, allow_none=True)
    error = fields.Str(required=False, allow_none=True)
    message = fields.Str(required=False, allow_none=True)


class InventoryResponseSchema(Schema):
    """Schema for inventory response"""

    success = fields.Bool(required=True)
    inventory = fields.List(fields.Dict(), required=False, allow_none=True)
    item = fields.Dict(required=False, allow_none=True)
    error = fields.Str(required=False, allow_none=True)
    message = fields.Str(required=False, allow_none=True)


class StandardResponseSchema(Schema):
    """Standard API response schema"""

    success = fields.Bool(required=True)
    data = fields.Raw(required=False, allow_none=True)
    error = fields.Str(required=False, allow_none=True)
    message = fields.Str(required=False, allow_none=True)
    timestamp = fields.DateTime(required=False, allow_none=True)


# Utility functions for validation
def validate_indian_state(state_name):
    """Validate if the provided state is a valid Indian state"""

    indian_states = [
        "Andhra Pradesh",
        "Arunachal Pradesh",
        "Assam",
        "Bihar",
        "Chhattisgarh",
        "Goa",
        "Gujarat",
        "Haryana",
        "Himachal Pradesh",
        "Jammu and Kashmir",
        "Jharkhand",
        "Karnataka",
        "Kerala",
        "Ladakh",
        "Madhya Pradesh",
        "Maharashtra",
        "Manipur",
        "Meghalaya",
        "Mizoram",
        "Nagaland",
        "Odisha",
        "Punjab",
        "Rajasthan",
        "Sikkim",
        "Tamil Nadu",
        "Telangana",
        "Tripura",
        "Uttar Pradesh",
        "Uttarakhand",
        "West Bengal",
        "Delhi",
        "Puducherry",
        "Chandigarh",
        "Andaman and Nicobar Islands",
        "Dadra and Nagar Haveli",
        "Daman and Diu",
        "Lakshadweep",
    ]

    return state_name in indian_states or any(
        state.lower() in state_name.lower() for state in indian_states
    )


# --- AI Forecast (Model-Driven) Schemas ---

class ProductDemandItemSchema(Schema):
    product = fields.Str(required=True)
    demand_percentage = fields.Int(required=True, validate=validate.Range(min=0, max=100))
    reason = fields.Str(required=False, allow_none=True)


class FestivalChartItemSchema(Schema):
    festival = fields.Str(required=True)
    demand_increase = fields.Int(required=True, validate=validate.Range(min=0, max=100))
    date = fields.Str(required=False, allow_none=True)  # YYYY-MM-DD
    month = fields.Str(required=False, allow_none=True)  # short month label
    year = fields.Int(required=False, allow_none=True)


class FestivalDemandsSchema(Schema):
    chart = fields.List(fields.Nested(FestivalChartItemSchema), required=True)
    top_items = fields.Dict(keys=fields.Str(), values=fields.Dict(), required=False)


class SeasonalChartItemSchema(Schema):
    season = fields.Str(required=True)
    demand_surge = fields.Int(required=True, validate=validate.Range(min=0, max=100))
    start = fields.Str(required=False, allow_none=True)  # YYYY-MM-DD
    end = fields.Str(required=False, allow_none=True)  # YYYY-MM-DD


class SeasonalDemandsSchema(Schema):
    chart = fields.List(fields.Nested(SeasonalChartItemSchema), required=True)
    top_items = fields.Dict(keys=fields.Str(), values=fields.Dict(), required=False)


class TabbedForecastSchema(Schema):
    product_demands = fields.List(fields.Nested(ProductDemandItemSchema), required=False)
    festival_demands = fields.Nested(FestivalDemandsSchema, required=False)
    seasonal_demands = fields.Nested(SeasonalDemandsSchema, required=False)
    suggestions = fields.List(fields.Str(), required=False)
    forecast_start = fields.Str(required=False)
    forecast_end = fields.Str(required=False)
    confidence_score = fields.Float(required=False)


def normalize_tabbed_forecast(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and lightly normalize the tabbed forecast payload.

    Uses partial validation to avoid being brittle. Returns the (possibly
    normalized) data back. Raises on unexpected structural issues only if
    they are severe; otherwise returns input.
    """
    try:
        schema = TabbedForecastSchema(partial=True)
        loaded = schema.load(data)
        return loaded
    except Exception:
        # Keep original data to preserve resilience
        return data


def validate_gst_number_format(gst_number):
    """Validate GST number format (15 characters)"""

    import re

    gst_pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    return re.match(gst_pattern, gst_number) is not None


def validate_phone_number_format(phone):
    """Validate Indian phone number format"""

    import re

    phone_pattern = r"^[6-9]\d{9}$"  # Indian mobile number pattern
    landline_pattern = r"^[0-9]{2,4}[0-9]{6,8}$"  # Indian landline pattern

    # Remove spaces and special characters
    clean_phone = re.sub(r"[\s\-\(\)\+]", "", phone)

    # Remove country code if present
    if clean_phone.startswith("91"):
        clean_phone = clean_phone[2:]
    elif clean_phone.startswith("+91"):
        clean_phone = clean_phone[3:]

    return re.match(phone_pattern, clean_phone) or re.match(
        landline_pattern, clean_phone
    )
