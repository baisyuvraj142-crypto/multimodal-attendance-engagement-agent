from typing import List, Dict, Any
from core.recommendations_engine import RecommendationsEngine
from core.llm_insights import LLMInsightGenerator

class AISuggestionService:
    """
    Coordinates rule-based real-time suggestions and LLM pedagogical insights.
    """
    def __init__(self):
        self.rules_engine = RecommendationsEngine()
        self.llm_generator = LLMInsightGenerator()

    def process_frame_suggestions(
        self,
        fused_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        trend_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        # 1. Rule-based suggestions
        rule_suggestions = self.rules_engine.evaluate(fused_data, engagement_data, trend_data)
        
        # 2. Contextual pedagogical insight
        context = {
            "engagement_score": engagement_data.get("overall_score", 0.0),
            "students_present": fused_data.get("students_present", 0),
            "audio_state": fused_data.get("audio_state", "silence"),
            "recent_suggestions": rule_suggestions
        }
        live_insight = self.llm_generator.generate_live_insight(context)

        return {
            "suggestions": rule_suggestions,
            "live_insight": live_insight
        }
