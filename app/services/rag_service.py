from typing import Dict, List, Any, Optional
import json


class RAGService:
    """Retrieval-Augmented Generation service for Indian retail intelligence"""

    def __init__(self):
        self.knowledge_base = self._initialize_knowledge_base()

    def query_knowledge_base(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query the retail knowledge base with RAG approach"""

        # Retrieve relevant documents
        relevant_docs = self._retrieve_documents(query, context)

        # Generate response using retrieved context
        response = self._generate_response(query, relevant_docs, context)

        return {
            "query": query,
            "response": response,
            "sources": relevant_docs,
            "confidence": self._calculate_confidence(query, relevant_docs),
        }

    def get_market_insights(self, business_type: str, location: str) -> Dict[str, Any]:
        """Get specific market insights for business type and location"""

        insights = {
            "market_size": self._get_market_size(business_type, location),
            "growth_trends": self._get_growth_trends(business_type, location),
            "consumer_behavior": self._get_consumer_behavior(business_type, location),
            "competitive_landscape": self._get_competitive_landscape(
                business_type, location
            ),
            "seasonal_patterns": self._get_seasonal_patterns(business_type, location),
            "regulatory_factors": self._get_regulatory_factors(business_type, location),
        }

        return insights

    def get_festival_intelligence(
        self, festivals: List[str], business_type: str
    ) -> Dict[str, Any]:
        """Get detailed festival impact intelligence"""

        festival_data = {}

        for festival in festivals:
            festival_data[festival] = {
                "impact_level": self._get_festival_impact_level(
                    festival, business_type
                ),
                "duration": self._get_festival_duration(festival),
                "preparation_time": self._get_preparation_time(festival, business_type),
                "key_products": self._get_festival_products(festival, business_type),
                "marketing_strategy": self._get_festival_marketing_strategy(
                    festival, business_type
                ),
                "inventory_recommendations": self._get_festival_inventory_recommendations(
                    festival, business_type
                ),
            }

        return festival_data

    def get_supply_chain_insights(
        self, business_scale: str, location: str
    ) -> Dict[str, Any]:
        """Get supply chain insights for business scale and location"""

        return {
            "supplier_network": self._get_supplier_network(business_scale, location),
            "logistics_options": self._get_logistics_options(business_scale, location),
            "cost_structure": self._get_cost_structure(business_scale, location),
            "risk_factors": self._get_supply_chain_risks(business_scale, location),
            "optimization_opportunities": self._get_optimization_opportunities(
                business_scale, location
            ),
            "technology_recommendations": self._get_technology_recommendations(
                business_scale
            ),
        }

    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """Initialize the Indian retail knowledge base"""

        return {
            "market_data": {
                "Indian_retail_market_size": "₹75 lakh crore (2024)",
                "growth_rate": "12-15% annually",
                "msme_contribution": "45% of total retail",
                "online_penetration": "8.5% and growing",
            },
            "festival_calendar": {
                "Diwali": {
                    "impact": "Very High",
                    "duration": "5 days",
                    "preparation": "6-8 weeks",
                    "categories_affected": [
                        "Electronics",
                        "Clothing",
                        "Jewelry",
                        "Sweets",
                        "Decorations",
                    ],
                },
                "Dussehra": {
                    "impact": "High",
                    "duration": "10 days",
                    "preparation": "4 weeks",
                    "categories_affected": ["Clothing", "Gifts", "Religious items"],
                },
            },
            "seasonal_patterns": {
                "monsoon": {
                    "months": [6, 7, 8, 9],
                    "impact": "Reduced footfall, increased essential goods",
                    "opportunities": ["Umbrella", "Rainwear", "Indoor entertainment"],
                },
                "winter": {
                    "months": [12, 1, 2],
                    "impact": "Festival season, wedding season",
                    "opportunities": [
                        "Warm clothing",
                        "Gift items",
                        "Wedding supplies",
                    ],
                },
            },
            "business_intelligence": {
                "Grocery Store": {
                    "key_success_factors": [
                        "Location",
                        "Fresh produce",
                        "Local preferences",
                    ],
                    "challenges": [
                        "Competition from online",
                        "Inventory management",
                        "Perishable goods",
                    ],
                    "opportunities": [
                        "Home delivery",
                        "Bulk sales",
                        "Community engagement",
                    ],
                },
                "Electronics Store": {
                    "key_success_factors": [
                        "Product knowledge",
                        "After-sales service",
                        "Competitive pricing",
                    ],
                    "challenges": [
                        "Online competition",
                        "Technology changes",
                        "High inventory costs",
                    ],
                    "opportunities": [
                        "Trade-in programs",
                        "Extended warranties",
                        "Smart home solutions",
                    ],
                },
            },
        }

    def _retrieve_documents(
        self, query: str, context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from knowledge base"""

        # Simple keyword-based retrieval (in production, use vector search)
        query_lower = query.lower()
        relevant_docs = []

        # Search in different categories
        if any(
            word in query_lower for word in ["festival", "diwali", "dussehra", "holi"]
        ):
            relevant_docs.extend(self._get_festival_documents(query_lower))

        if any(word in query_lower for word in ["market", "size", "growth", "trend"]):
            relevant_docs.extend(self._get_market_documents(query_lower))

        if any(
            word in query_lower for word in ["seasonal", "monsoon", "winter", "summer"]
        ):
            relevant_docs.extend(self._get_seasonal_documents(query_lower))

        if any(
            word in query_lower
            for word in ["business", "grocery", "electronics", "clothing"]
        ):
            relevant_docs.extend(self._get_business_documents(query_lower, context))

        return relevant_docs[:5]  # Return top 5 relevant documents

    def _generate_response(
        self,
        query: str,
        relevant_docs: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Generate response using retrieved documents"""

        if not relevant_docs:
            return "I don't have specific information about that query in my current knowledge base."

        # Simple response generation (in production, use language model)
        response_parts = []

        for doc in relevant_docs:
            if doc["relevance_score"] > 0.7:
                response_parts.append(doc["content"])

        if response_parts:
            return " ".join(response_parts)
        else:
            return "Based on available information, " + relevant_docs[0]["content"]

    def _calculate_confidence(
        self, query: str, relevant_docs: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for the response"""

        if not relevant_docs:
            return 0.0

        avg_relevance = sum(doc["relevance_score"] for doc in relevant_docs) / len(
            relevant_docs
        )
        return min(avg_relevance * 1.2, 1.0)  # Cap at 1.0

    def _get_festival_documents(self, query: str) -> List[Dict[str, Any]]:
        """Get festival-related documents"""

        docs = []

        if "diwali" in query:
            docs.append(
                {
                    "content": "Diwali is the biggest retail opportunity in India, driving 50-70% sales increase across categories like electronics, clothing, jewelry, and sweets. Preparation should begin 6-8 weeks in advance.",
                    "relevance_score": 0.9,
                    "source": "Festival Intelligence Database",
                }
            )

        if "festival" in query:
            docs.append(
                {
                    "content": "Indian festivals significantly impact retail demand with Diwali, Dussehra, and regional festivals being major drivers. Festival seasons can increase sales by 40-70% for most retail categories.",
                    "relevance_score": 0.8,
                    "source": "Indian Retail Research",
                }
            )

        return docs

    def _get_market_documents(self, query: str) -> List[Dict[str, Any]]:
        """Get market-related documents"""

        return [
            {
                "content": "The Indian retail market is valued at ₹75 lakh crore with 12-15% annual growth. MSME retailers contribute 45% of the total market, making them crucial for the economy.",
                "relevance_score": 0.85,
                "source": "Indian Retail Market Analysis 2024",
            }
        ]

    def _get_seasonal_documents(self, query: str) -> List[Dict[str, Any]]:
        """Get seasonal pattern documents"""

        docs = []

        if "monsoon" in query:
            docs.append(
                {
                    "content": "Monsoon season (June-September) reduces footfall but increases demand for essentials, umbrellas, and indoor entertainment products.",
                    "relevance_score": 0.8,
                    "source": "Seasonal Demand Analysis",
                }
            )

        return docs

    def _get_business_documents(
        self, query: str, context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get business-specific documents"""

        business_type = context.get("business_type") if context else None

        docs = []

        if business_type in self.knowledge_base["business_intelligence"]:
            business_info = self.knowledge_base["business_intelligence"][business_type]
            docs.append(
                {
                    "content": f"For {business_type}, key success factors include {', '.join(business_info['key_success_factors'])}. Main challenges are {', '.join(business_info['challenges'])}.",
                    "relevance_score": 0.9,
                    "source": f"{business_type} Business Intelligence",
                }
            )

        return docs

    # Helper methods for specific insights
    def _get_market_size(self, business_type: str, location: str) -> str:
        return f"The {business_type} market in {location} is part of India's ₹75 lakh crore retail sector, growing at 12-15% annually."

    def _get_growth_trends(self, business_type: str, location: str) -> List[str]:
        return [
            "Digital integration accelerating post-COVID",
            "Premiumization trend in urban markets",
            "Sustainability becoming important",
            "Local and regional preferences strengthening",
        ]

    def _get_consumer_behavior(
        self, business_type: str, location: str
    ) -> Dict[str, str]:
        return {
            "price_sensitivity": "High for essentials, moderate for lifestyle",
            "brand_loyalty": "Moderate, increasing with quality experience",
            "shopping_frequency": "Daily to weekly for essentials",
            "digital_adoption": "Rapidly increasing across age groups",
        }

    def _get_competitive_landscape(
        self, business_type: str, location: str
    ) -> Dict[str, Any]:
        return {
            "intensity": "High",
            "key_players": [
                "Local retailers",
                "Regional chains",
                "E-commerce platforms",
                "Organized retail",
            ],
            "competitive_advantages": [
                "Personal service",
                "Local knowledge",
                "Flexible pricing",
                "Community relationships",
            ],
            "threats": [
                "Online competition",
                "Large format stores",
                "Supply chain efficiency",
            ],
        }

    def _get_seasonal_patterns(
        self, business_type: str, location: str
    ) -> Dict[str, str]:
        return {
            "peak_seasons": "Festival periods (Oct-Nov), Wedding season (Nov-Feb)",
            "low_seasons": "Monsoon period (Jun-Sep), Post-festival normalization",
            "growth_opportunities": "Festival preparations, Seasonal product launches",
        }

    def _get_regulatory_factors(self, business_type: str, location: str) -> List[str]:
        return [
            "GST compliance requirements",
            "Local municipal licenses",
            "Food safety regulations (if applicable)",
            "Labor law compliance",
            "Environmental regulations",
        ]

    def _get_festival_impact_level(self, festival: str, business_type: str) -> str:
        impact_map = {
            ("Diwali", "Electronics Store"): "Very High",
            ("Diwali", "Clothing Store"): "Very High",
            ("Diwali", "Grocery Store"): "High",
            ("Dussehra", "Clothing Store"): "High",
            ("Holi", "Grocery Store"): "Medium",
        }
        return impact_map.get((festival, business_type), "Medium")

    def _get_festival_duration(self, festival: str) -> str:
        duration_map = {
            "Diwali": "5 days",
            "Dussehra": "10 days",
            "Holi": "2 days",
            "Ganesh Chaturthi": "11 days",
        }
        return duration_map.get(festival, "1-2 days")

    def _get_preparation_time(self, festival: str, business_type: str) -> str:
        if festival == "Diwali":
            return "6-8 weeks"
        elif festival in ["Dussehra", "Ganesh Chaturthi"]:
            return "4 weeks"
        else:
            return "2-3 weeks"

    def _get_festival_products(self, festival: str, business_type: str) -> List[str]:
        product_map = {
            ("Diwali", "Electronics Store"): [
                "LED lights",
                "Sound systems",
                "TVs",
                "Mobile phones",
                "Laptops",
            ],
            ("Diwali", "Clothing Store"): [
                "Ethnic wear",
                "Party wear",
                "Traditional clothing",
                "Accessories",
            ],
            ("Diwali", "Grocery Store"): [
                "Sweets",
                "Dry fruits",
                "Pooja items",
                "Decorative items",
                "Gift hampers",
            ],
        }
        return product_map.get((festival, business_type), ["Festival-specific items"])

    def _get_festival_marketing_strategy(
        self, festival: str, business_type: str
    ) -> List[str]:
        return [
            "Start marketing 6 weeks before festival",
            "Create festival-themed displays",
            "Offer bundle deals and discounts",
            "Partner with local community events",
            "Use digital marketing for broader reach",
        ]

    def _get_festival_inventory_recommendations(
        self, festival: str, business_type: str
    ) -> List[str]:
        return [
            "Increase inventory by 40-60% for key categories",
            "Ensure adequate storage space",
            "Coordinate with suppliers for timely delivery",
            "Plan for post-festival inventory management",
            "Consider local preferences and variations",
        ]

    def _get_supplier_network(
        self, business_scale: str, location: str
    ) -> Dict[str, Any]:
        return {
            "local_suppliers": "Strong network available in most Indian cities",
            "regional_distributors": "Well-established for MSME segment",
            "national_suppliers": "Available for established businesses",
            "digital_platforms": "Growing B2B platforms connecting suppliers",
        }

    def _get_logistics_options(self, business_scale: str, location: str) -> List[str]:
        return [
            "Local delivery partners",
            "Regional logistics companies",
            "Third-party logistics providers",
            "Self-delivery options",
            "E-commerce fulfillment services",
        ]

    def _get_cost_structure(self, business_scale: str, location: str) -> Dict[str, str]:
        return {
            "procurement_cost": "60-70% of total costs",
            "logistics_cost": "8-12% of total costs",
            "storage_cost": "3-5% of total costs",
            "technology_cost": "1-3% of total costs",
        }

    def _get_supply_chain_risks(self, business_scale: str, location: str) -> List[str]:
        return [
            "Supplier reliability and quality issues",
            "Transportation and logistics delays",
            "Inventory management challenges",
            "Seasonal demand fluctuations",
            "Economic and regulatory changes",
        ]

    def _get_optimization_opportunities(
        self, business_scale: str, location: str
    ) -> List[str]:
        return [
            "Implement inventory management systems",
            "Develop strategic supplier relationships",
            "Optimize delivery routes and schedules",
            "Use demand forecasting tools",
            "Adopt digital procurement processes",
        ]

    def _get_technology_recommendations(self, business_scale: str) -> List[str]:
        if business_scale == "Micro":
            return [
                "Basic POS systems",
                "Simple inventory tracking",
                "WhatsApp Business",
                "Digital payments",
            ]
        elif business_scale == "Small":
            return [
                "ERP systems",
                "CRM software",
                "E-commerce integration",
                "Analytics tools",
            ]
        else:  # Medium
            return [
                "Advanced ERP",
                "AI-powered forecasting",
                "Supply chain automation",
                "Data analytics platforms",
            ]
