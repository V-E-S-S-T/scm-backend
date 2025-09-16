from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.services.demand_service import DemandService

router = APIRouter()


class ScenarioRequest(BaseModel):
    baseSales: float = Field(..., description="Base monthly sales in INR")
    priceChange: float = Field(..., description="Price change percentage")
    marketingSpend: float = Field(0, description="Marketing spend in INR")
    seasonalFactor: float = Field(1.0, description="Seasonal factor (1.0 = normal)")
    competitorAction: str = Field(..., description="Competitor action type")


class ScenarioResponse(BaseModel):
    success: bool
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None


@router.post("/analyze", response_model=ScenarioResponse)
async def analyze_scenario(scenario: ScenarioRequest):
    """
    Analyze what-if scenario for business strategy
    """

    # Validate inputs to return 400 per tests instead of 422
    if scenario.baseSales <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid baseSales",
                "message": "baseSales must be greater than 0",
            },
        )
    if not (-50 <= scenario.priceChange <= 100):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid priceChange",
                "message": "priceChange must be between -50 and 100",
            },
        )
    if scenario.marketingSpend < 0:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid marketingSpend",
                "message": "marketingSpend must be >= 0",
            },
        )
    if not (0.1 <= scenario.seasonalFactor <= 5.0):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid seasonalFactor",
                "message": "seasonalFactor must be between 0.1 and 5.0",
            },
        )

    # Validate competitor action
    valid_actions = ["none", "aggressive", "passive"]
    if scenario.competitorAction not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid competitor action",
                "message": f"Competitor action must be one of: {', '.join(valid_actions)}",
            },
        )

    try:
        demand_service = DemandService()

        scenario_data = scenario.dict()
        results = demand_service.analyze_scenario(scenario_data)

        return ScenarioResponse(
            success=True,
            results=results,
            message="Scenario analysis completed successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Scenario analysis failed",
                "message": str(e),
            },
        )


@router.get("/templates")
async def get_scenario_templates():
    """
    Get predefined scenario templates
    """

    templates = [
        {
            "name": "Festival Season Boost",
            "description": "Model festival season demand with increased marketing",
            "parameters": {
                "priceChange": 5,
                "marketingSpend": 50000,
                "seasonalFactor": 1.8,
                "competitorAction": "passive",
            },
        },
        {
            "name": "Competitive Price War",
            "description": "Response to aggressive competitor pricing",
            "parameters": {
                "priceChange": -15,
                "marketingSpend": 75000,
                "seasonalFactor": 1.0,
                "competitorAction": "aggressive",
            },
        },
        {
            "name": "Premium Positioning",
            "description": "Test premium pricing with quality marketing",
            "parameters": {
                "priceChange": 20,
                "marketingSpend": 100000,
                "seasonalFactor": 1.0,
                "competitorAction": "none",
            },
        },
        {
            "name": "Economic Downturn",
            "description": "Model performance during economic slowdown",
            "parameters": {
                "priceChange": -10,
                "marketingSpend": 25000,
                "seasonalFactor": 0.7,
                "competitorAction": "aggressive",
            },
        },
        {
            "name": "Market Expansion",
            "description": "Aggressive growth strategy scenario",
            "parameters": {
                "priceChange": 0,
                "marketingSpend": 150000,
                "seasonalFactor": 1.2,
                "competitorAction": "passive",
            },
        },
    ]

    return {
        "success": True,
        "templates": templates,
        "count": len(templates),
        "message": "Scenario templates retrieved successfully",
    }


@router.post("/compare")
async def compare_scenarios(scenarios: list[ScenarioRequest]):
    """
    Compare multiple scenarios side by side
    """

    if len(scenarios) < 2 or len(scenarios) > 5:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid scenario count",
                "message": "Please provide 2-5 scenarios for comparison",
            },
        )

    try:
        demand_service = DemandService()

        comparison_results = []

        for i, scenario in enumerate(scenarios):
            scenario_data = scenario.dict()
            result = demand_service.analyze_scenario(scenario_data)
            result["scenario_name"] = f"Scenario {i + 1}"
            comparison_results.append(result)

        # Calculate best and worst scenarios
        best_scenario = max(comparison_results, key=lambda x: x.get("totalImpact", 0))
        worst_scenario = min(comparison_results, key=lambda x: x.get("totalImpact", 0))

        return {
            "success": True,
            "comparison": {
                "scenarios": comparison_results,
                "best_scenario": best_scenario["scenario_name"],
                "worst_scenario": worst_scenario["scenario_name"],
                "impact_range": {
                    "best": best_scenario.get("totalImpact", 0),
                    "worst": worst_scenario.get("totalImpact", 0),
                },
            },
            "message": f"Compared {len(scenarios)} scenarios successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Scenario comparison failed",
                "message": str(e),
            },
        )


@router.get("/insights/{business_type}")
async def get_scenario_insights(business_type: str, location: str = "Karnataka"):
    """
    Get scenario insights specific to business type and location
    """

    try:
        demand_service = DemandService()

        insights = demand_service.get_scenario_insights(business_type, location)

        return {
            "success": True,
            "insights": insights,
            "business_type": business_type,
            "location": location,
            "message": "Scenario insights retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve scenario insights",
                "message": str(e),
            },
        )
