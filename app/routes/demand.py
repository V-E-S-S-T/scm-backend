from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.services.demand_service import DemandService
from sqlalchemy.orm import Session
from app.utils.db import get_db
from app.models.db_models import Business, DemandForecast
from app.utils.config import get_config

router = APIRouter()


class ForecastRequest(BaseModel):
    businessName: Optional[str] = Field(None, max_length=255)
    businessType: str = Field(
        ..., description="Business type (Grocery Store, Electronics Store, etc.)"
    )
    businessScale: str = Field(
        ..., description="Business scale (Micro, Small, Medium, Large)"
    )
    location: str = Field(..., description="Indian state location")
    state: Optional[str] = Field(None, description="State name (separate field if needed)")
    currentSales: float = Field(
        ..., gt=1000, description="Current monthly sales in INR"
    )
    forecastPeriod: Optional[float] = Field(
        6,
        gt=0,
        le=36,
        description="Forecast period in months from today; supports fractions (e.g., 0.25 ≈ 1 week)",
    )


class ForecastResponse(BaseModel):
    success: bool
    forecast: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None


class SuggestionRequest(BaseModel):
    businessName: Optional[str] = Field(None, max_length=255)
    businessType: str
    businessScale: str
    location: str
    currentSales: float
    topProducts: Optional[List[str]] = None


class SuggestionResponse(BaseModel):
    success: bool
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None


@router.post("/forecast")
async def generate_forecast(request: ForecastRequest, db: Session = Depends(get_db)):
    """
    Generate demand forecast for product, festival, and seasonal demands (tabbed UI).
    """
    try:
        supported_business_types = [
            "Grocery Store",
            "Electronics Store",
            "Clothing Store",
            "Medical Store",
            "Cosmetics Store",
            "Food & Beverage",
        ]
        supported_scales = ["Micro", "Small", "Medium", "Large"]

        if request.businessType not in supported_business_types:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Invalid business type",
                    "message": f"businessType must be one of: {', '.join(supported_business_types)}",
                },
            )

        if request.businessScale not in supported_scales:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Invalid business scale",
                    "message": f"businessScale must be one of: {', '.join(supported_scales)}",
                },
            )

        demand_service = DemandService()
        payload = request.dict()
        try:
            tabbed_data = await demand_service.generate_tabbed_forecast(payload)
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail={
                    "success": False,
                    "error": "AI model output incomplete",
                    "message": str(e),
                },
            )

        state = payload.get("state") or payload.get("location")
        biz_name = payload.get("businessName") or f"{payload['businessType']} @ {state}"
        business = (
            db.query(Business)
            .filter(
                Business.name == biz_name,
                Business.type == payload["businessType"],
                Business.location == payload["location"],
                Business.state == state,
            )
            .first()
        )
        if not business:
            business = Business(
                name=biz_name,
                type=payload["businessType"],
                scale=payload["businessScale"],
                location=payload["location"],
                state=state,
            )
            db.add(business)
            db.flush()

        model_used = "Gemini 2.5 Pro" if get_config().gemini_api_key else "Fallback"
        recommendations = tabbed_data.get("suggestions") or []
        confidence = tabbed_data.get("confidence_score")

        monthly_blob = {
            "forecast_start": tabbed_data.get("forecast_start"),
            "forecast_end": tabbed_data.get("forecast_end"),
            "product_demands": tabbed_data.get("product_demands"),
            "festival_demands": tabbed_data.get("festival_demands"),
            "seasonal_demands": tabbed_data.get("seasonal_demands"),
        }

        df = DemandForecast(
            business_id=business.id,
            forecast_period_months=int(payload.get("forecastPeriod") or 6),
            current_sales=payload["currentSales"],
            monthly_projections=monthly_blob,
            recommendations=recommendations,
            confidence_score=confidence,
            model_used=model_used,
            generated_by="AI",
        )
        db.add(df)
        db.commit()
        db.refresh(df)

        return {"success": True, "forecast": tabbed_data, "forecastId": df.id}
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        print(f"Forecast generation error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Forecast generation failed",
                "message": "Unable to generate forecast. Please try again later.",
            },
        )


@router.post("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(request: SuggestionRequest):
    """
    Return suggestions derived from the same unified forecast prompt.
    """
    try:
        demand_service = DemandService()
        data = request.dict()
        forecast = await demand_service.generate_tabbed_forecast(
            {
                "businessName": data.get("businessName"),
                "businessType": data["businessType"],
                "businessScale": data["businessScale"],
                "location": data["location"],
                "currentSales": data["currentSales"],
                "forecastPeriod": 6,
            }
        )
        return {"success": True, "suggestions": forecast.get("suggestions", [])}
    except Exception as e:
        import traceback

        print(f"Suggestions generation error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Suggestions generation failed",
                "message": "Unable to generate suggestions. Please try again later.",
            },
        )


@router.get("/seasonal-patterns")
async def get_seasonal_patterns(type: str, location: str):
    """Get seasonal demand patterns for business type and location"""

    try:
        demand_service = DemandService()
        patterns = demand_service.get_seasonal_patterns(type, location)

        return {
            "success": True,
            "patterns": patterns,
            "business_type": type,
            "location": location,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve seasonal patterns",
                "message": str(e),
            },
        )


@router.get("/festival-calendar")
async def get_festival_calendar(year: int = 2025):
    """Get Indian festival calendar with retail impact analysis"""

    try:
        demand_service = DemandService()
        calendar = demand_service.get_festival_calendar(year)

        return {
            "success": True,
            "calendar": calendar,
            "year": year,
            "market": "Indian Retail",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve festival calendar",
                "message": str(e),
            },
        )


@router.get("/business-types")
async def get_business_types():
    """Get supported business types and scales"""

    business_types = [
        "Grocery Store",
        "Electronics Store",
        "Clothing Store",
        "Medical Store",
        "Cosmetics Store",
        "Food & Beverage",
    ]

    business_scales = ["Micro", "Small", "Medium", "Large"]

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
    ]

    return {
        "success": True,
        "business_types": business_types,
        "business_scales": business_scales,
        "locations": indian_states,
        "classification": "MSME (Micro, Small, Medium Enterprise)",
    }


@router.get("/forecast-history")
async def get_forecast_history(
    business_type: Optional[str] = None, limit: int = 10, db: Session = Depends(get_db)
):
    """Get historical forecast data from SQLite"""

    try:
        q = db.query(DemandForecast, Business).join(
            Business, Business.id == DemandForecast.business_id
        )
        if business_type:
            q = q.filter(Business.type == business_type)
        rows = (
            q.order_by(DemandForecast.created_at.desc())
            .limit(max(1, min(limit, 100)))
            .all()
        )
        history = []
        for df, biz in rows:
            history.append(
                {
                    "id": df.id,
                    "business_type": biz.type,
                    "location": biz.location,
                    "state": getattr(biz, "state", None),
                    "forecast_date": (
                        df.created_at.isoformat() if df.created_at else None
                    ),
                    "period": f"{df.forecast_period_months} months",
                    "confidence": df.confidence_score,
                    "model_used": df.model_used,
                    "business_name": biz.name,
                }
            )
        return {"success": True, "history": history, "count": len(history)}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve forecast history",
                "message": str(e),
            },
        )


@router.get("/forecast/{forecast_id}")
async def get_forecast(forecast_id: int, db: Session = Depends(get_db)):
    """Retrieve a saved forecast by its ID."""
    try:
        df = db.query(DemandForecast).filter(DemandForecast.id == forecast_id).first()
        if not df:
            raise HTTPException(
                status_code=404, detail={"success": False, "error": "Not found"}
            )
        blob = df.monthly_projections or {}
        forecast = {
            "product_demands": blob.get("product_demands"),
            "festival_demands": blob.get("festival_demands"),
            "seasonal_demands": blob.get("seasonal_demands"),
            "suggestions": df.recommendations or [],
            "forecast_start": blob.get("forecast_start"),
            "forecast_end": blob.get("forecast_end"),
        }
        try:
            biz = db.query(Business).filter(Business.id == df.business_id).first()
            if biz and getattr(biz, 'state', None):
                forecast["state"] = biz.state
        except Exception:
            pass
        if df.confidence_score is not None:
            forecast["confidence_score"] = df.confidence_score
        return {"success": True, "forecast": forecast, "forecastId": df.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve forecast",
                "message": str(e),
            },
        )
