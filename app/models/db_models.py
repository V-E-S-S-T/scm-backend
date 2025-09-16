from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class Business(Base):
    """Business entity model"""

    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(100), nullable=False, index=True)
    scale = Column(String(50), nullable=False)  # Micro, Small, Medium
    location = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=True, index=True)
    owner_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    registration_number = Column(String(100), nullable=True)
    gst_number = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    demand_forecasts = relationship("DemandForecast", back_populates="business")
    inventory_items = relationship("InventoryItem", back_populates="business")
    shipments = relationship("Shipment", back_populates="business")

    def __repr__(self):
        return (
            f"<Business(name='{self.name}', type='{self.type}', scale='{self.scale}')>"
        )


class DemandForecast(Base):
    """Demand forecast model"""

    __tablename__ = "demand_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)

    # Forecast parameters
    forecast_period_months = Column(Integer, default=6)
    current_sales = Column(Float, nullable=False)

    # AI-generated content
    seasonal_analysis = Column(Text, nullable=True)
    festival_impact = Column(Text, nullable=True)
    monthly_projections = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Metadata
    model_used = Column(
        String(100), nullable=True
    )  # 'Gemini 2.5 Pro' or 'Statistical Model'
    generated_by = Column(String(50), default="AI")
    forecast_date = Column(DateTime(timezone=True), server_default=func.now())

    # Tracking accuracy
    actual_results = Column(JSON, nullable=True)
    accuracy_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    business = relationship("Business", back_populates="demand_forecasts")
    accuracy_metrics = relationship("ForecastAccuracy", back_populates="forecast")

    def __repr__(self):
        return f"<DemandForecast(business_id={self.business_id}, confidence={self.confidence_score})>"


class InventoryItem(Base):
    """Inventory item model"""

    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)

    # Item details
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    sku = Column(String(100), nullable=True, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Stock levels
    current_stock = Column(Integer, nullable=False, default=0)
    min_stock_level = Column(Integer, nullable=False)
    max_stock_level = Column(Integer, nullable=False)
    reorder_point = Column(Integer, nullable=True)

    # Pricing
    unit_cost = Column(Float, nullable=True)
    selling_price = Column(Float, nullable=True)
    markup_percentage = Column(Float, nullable=True)

    # Supplier information
    supplier = Column(String(255), nullable=True)
    supplier_contact = Column(String(255), nullable=True)

    # Tracking
    last_restock_date = Column(DateTime(timezone=True), nullable=True)
    last_sale_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    business = relationship("Business", back_populates="inventory_items")

    @property
    def stock_status(self):
        """Calculate stock status"""
        if self.current_stock <= self.min_stock_level * 0.5:
            return "critical"
        elif self.current_stock <= self.min_stock_level:
            return "low"
        elif self.current_stock >= self.max_stock_level * 1.2:
            return "overstock"
        else:
            return "healthy"

    def __repr__(self):
        return f"<InventoryItem(name='{self.name}', stock={self.current_stock}, status='{self.stock_status}')>"


class Shipment(Base):
    """Shipment tracking model"""

    __tablename__ = "shipments"

    id = Column(String(20), primary_key=True, index=True)  # SHP-XXXXXXXX format
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)

    # Shipment details
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    status = Column(
        String(50), nullable=False, default="Processing"
    )  # Processing, In Transit, Delivered, Cancelled

    # Package information
    items_count = Column(Integer, nullable=True)
    total_weight = Column(Float, nullable=True)
    package_dimensions = Column(JSON, nullable=True)

    # Dates
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    shipped_date = Column(DateTime(timezone=True), nullable=True)
    estimated_delivery = Column(DateTime(timezone=True), nullable=True)
    actual_delivery = Column(DateTime(timezone=True), nullable=True)

    # Cost and tracking
    shipping_cost = Column(Float, nullable=True)
    tracking_number = Column(String(100), nullable=True)
    carrier = Column(String(100), nullable=True)

    # Additional information
    special_instructions = Column(Text, nullable=True)
    tracking_info = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    business = relationship("Business", back_populates="shipments")

    def __repr__(self):
        return f"<Shipment(id='{self.id}', status='{self.status}', destination='{self.destination}')>"


class ForecastAccuracy(Base):
    """Track forecast accuracy over time"""

    __tablename__ = "forecast_accuracy"

    id = Column(Integer, primary_key=True, index=True)
    forecast_id = Column(Integer, ForeignKey("demand_forecasts.id"), nullable=False)

    # Accuracy metrics
    predicted_sales = Column(Float, nullable=False)
    actual_sales = Column(Float, nullable=False)
    accuracy_percentage = Column(Float, nullable=False)
    absolute_error = Column(Float, nullable=False)

    # Period information
    forecast_month = Column(String(20), nullable=False)  # e.g., "Oct 2025"
    measurement_date = Column(DateTime(timezone=True), nullable=False)

    # Additional metrics
    prediction_confidence = Column(Float, nullable=True)
    factors_considered = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    forecast = relationship("DemandForecast", back_populates="accuracy_metrics")

    def __repr__(self):
        return f"<ForecastAccuracy(forecast_id={self.forecast_id}, accuracy={self.accuracy_percentage}%)>"


class BusinessMetrics(Base):
    """Business performance metrics"""

    __tablename__ = "business_metrics"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)

    # Sales metrics
    monthly_sales = Column(Float, nullable=True)
    quarterly_sales = Column(Float, nullable=True)
    yearly_sales = Column(Float, nullable=True)

    # Growth metrics
    month_over_month_growth = Column(Float, nullable=True)
    quarter_over_quarter_growth = Column(Float, nullable=True)
    year_over_year_growth = Column(Float, nullable=True)

    # Operational metrics
    inventory_turnover = Column(Float, nullable=True)
    gross_margin_percentage = Column(Float, nullable=True)
    customer_acquisition_cost = Column(Float, nullable=True)

    # Period
    metric_period = Column(
        String(20), nullable=False
    )  # 'monthly', 'quarterly', 'yearly'
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<BusinessMetrics(business_id={self.business_id}, period='{self.metric_period}')>"


class SeasonalPattern(Base):
    """Seasonal demand patterns for different business types"""

    __tablename__ = "seasonal_patterns"

    id = Column(Integer, primary_key=True, index=True)

    # Pattern identification
    business_type = Column(String(100), nullable=False, index=True)
    location = Column(String(100), nullable=False, index=True)

    # Seasonal data
    month = Column(Integer, nullable=False)  # 1-12
    seasonal_factor = Column(Float, nullable=False)  # Multiplier (1.0 = normal)
    demand_pattern = Column(String(50), nullable=False)  # 'high', 'medium', 'low'

    # Festival impact
    festival_impact = Column(Float, nullable=True)
    major_festivals = Column(JSON, nullable=True)

    # Additional context
    weather_impact = Column(String(100), nullable=True)
    cultural_factors = Column(JSON, nullable=True)

    # Data source
    data_source = Column(String(100), nullable=True)
    confidence_level = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<SeasonalPattern(type='{self.business_type}', month={self.month}, factor={self.seasonal_factor})>"


class UserSession(Base):
    """User session tracking (for future authentication)"""

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    user_identifier = Column(String(255), nullable=True)  # Email or username
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True)

    # Session data
    session_data = Column(JSON, nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Tracking
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<UserSession(session_id='{self.session_id[:8]}...', active={self.is_active})>"


# Database utility functions
def create_all_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables created successfully")


def drop_all_tables(engine):
    """Drop all database tables (for testing/reset)"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All database tables dropped")
