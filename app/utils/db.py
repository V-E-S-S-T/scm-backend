from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import os
from typing import Generator
from app.models.db_models import (
    Base,
    Business,
    DemandForecast,
    InventoryItem,
    Shipment,
    SeasonalPattern,
)
from app.utils.config import get_config


class DatabaseManager:
    """Database connection and session management"""

    def __init__(self):
        self.config = get_config()
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database connection"""

        database_url = os.getenv("DATABASE_URL", "sqlite:///ai_supplychain.db")

        if database_url.startswith("sqlite"):
            # SQLite configuration
            is_memory = database_url.endswith(":memory:") or database_url.endswith(
                ":///:memory:"
            )
            if is_memory:
                # In-memory DB: single connection shared, disable thread check
                self.engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
                )
            else:
                # File-based DB: use default pooling, disable thread check
                self.engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
                )
        else:
            # PostgreSQL configuration for production
            self.engine = create_engine(
                database_url,
                pool_size=int(os.getenv("DB_POOL_SIZE", 10)),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", 20)),
                echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            )

        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        print(f"✅ Database configured: {database_url.split('://')[0]}")

    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            # Lightweight migration: add missing columns for SQLite
            try:
                if str(self.engine.url).startswith("sqlite"):
                    with self.engine.connect() as conn:
                        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(businesses)"))]
                        if "state" not in cols:
                            conn.execute(text("ALTER TABLE businesses ADD COLUMN state VARCHAR(100)"))
                            print("✅ Migrated: added 'state' column to businesses")
            except Exception as mig_e:
                print(f"⚠️ Migration warning: {mig_e}")
            print("✅ Database tables created successfully")
            return True
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            return False

    def drop_tables(self):
        """Drop all database tables (for testing/reset)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            print("⚠️ All database tables dropped")
            return True
        except Exception as e:
            print(f"❌ Error dropping database tables: {e}")
            return False

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""

        db = self.SessionLocal()
        try:
            yield db
        except Exception as e:
            db.rollback()
            print(f"Database session error: {e}")
            raise
        finally:
            db.close()

    def get_session_dependency(self) -> Generator[Session, None, None]:
        """FastAPI dependency for database sessions"""

        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def test_connection(self) -> bool:
        """Test database connection"""

        try:
            with self.get_session() as db:
                db.execute(text("SELECT 1"))
                print("✅ Database connection successful")
                return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def seed_sample_data(self):
        """Seed database with sample data"""

        try:
            with self.get_session() as db:
                # Check if data already exists
                existing_business = db.query(Business).first()
                if existing_business:
                    print("ℹ️ Sample data already exists, skipping seed")
                    return

                # Create sample businesses
                businesses = [
                    Business(
                        name="Rajesh Electronics",
                        type="Electronics Store",
                        scale="Small",
                        location="Karnataka",
                        owner_name="Rajesh Kumar",
                        contact_email="rajesh@electronics.com",
                        contact_phone="9876543210",
                    ),
                    Business(
                        name="Priya Grocery Mart",
                        type="Grocery Store",
                        scale="Micro",
                        location="Maharashtra",
                        owner_name="Priya Sharma",
                        contact_email="priya@grocerymart.com",
                        contact_phone="9876543211",
                    ),
                    Business(
                        name="Fashion Hub",
                        type="Clothing Store",
                        scale="Medium",
                        location="Tamil Nadu",
                        owner_name="Arjun Menon",
                        contact_email="arjun@fashionhub.com",
                        contact_phone="9876543212",
                    ),
                ]

                for business in businesses:
                    db.add(business)

                db.flush()  # Get IDs for businesses

                # Create sample inventory items
                inventory_items = [
                    InventoryItem(
                        business_id=businesses[0].id,
                        name="Samsung Galaxy A54",
                        category="Electronics",
                        sku="SAM-A54-001",
                        current_stock=15,
                        min_stock_level=20,
                        max_stock_level=50,
                        unit_cost=15000.0,
                        selling_price=18000.0,
                        supplier="Electronics Distributor",
                    ),
                    InventoryItem(
                        business_id=businesses[1].id,
                        name="Basmati Rice 1kg",
                        category="Grocery",
                        sku="GRC-RICE-001",
                        current_stock=150,
                        min_stock_level=50,
                        max_stock_level=200,
                        unit_cost=80.0,
                        selling_price=120.0,
                        supplier="Local Rice Supplier",
                    ),
                    InventoryItem(
                        business_id=businesses[2].id,
                        name="Festival Kurta Set",
                        category="Clothing",
                        sku="CLT-KURTA-001",
                        current_stock=80,
                        min_stock_level=30,
                        max_stock_level=100,
                        unit_cost=800.0,
                        selling_price=1500.0,
                        supplier="Textile Manufacturer",
                    ),
                ]

                for item in inventory_items:
                    db.add(item)

                # Create sample seasonal patterns
                seasonal_patterns = [
                    SeasonalPattern(
                        business_type="Electronics Store",
                        location="Karnataka",
                        month=10,
                        seasonal_factor=1.6,
                        demand_pattern="high",
                        festival_impact=0.7,
                        major_festivals=["Dussehra", "Diwali"],
                    ),
                    SeasonalPattern(
                        business_type="Grocery Store",
                        location="Maharashtra",
                        month=11,
                        seasonal_factor=1.8,
                        demand_pattern="high",
                        festival_impact=0.8,
                        major_festivals=["Diwali", "Regional Festivals"],
                    ),
                ]

                for pattern in seasonal_patterns:
                    db.add(pattern)

                db.commit()
                print("✅ Sample data seeded successfully")
                print(f"   - Created {len(businesses)} sample businesses")
                print(f"   - Created {len(inventory_items)} sample inventory items")
                print(f"   - Created {len(seasonal_patterns)} seasonal patterns")

        except Exception as e:
            print(f"❌ Error seeding sample data: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()


def init_database():
    """Initialize database tables"""
    return db_manager.create_tables()


def seed_sample_data():
    """Seed database with sample data"""
    return db_manager.seed_sample_data()


def get_database_session():
    """Get database session (FastAPI dependency)"""
    return db_manager.get_session_dependency()


def test_database_connection():
    """Test database connection"""
    return db_manager.test_connection()


# FastAPI database dependency
def get_db() -> Generator[Session, None, None]:
    """FastAPI database dependency that yields a Session"""
    db = db_manager.SessionLocal()
    try:
        yield db
    finally:
        db.close()
