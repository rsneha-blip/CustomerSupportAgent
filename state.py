# state.py
from typing import Dict, Optional

class AgentState:
    def __init__(self):
        # Track attempts by problem category + order
        # Format: "problem_category:order_id" -> attempt_count
        self.attempts_by_problem: Dict[str, int] = {}
        
        # Current context
        self.current_order_id: Optional[str] = None
        self.current_problem_category: Optional[str] = None
    
    def record_attempt(self, problem_category: str, order_id: str):
        """Record an attempt for a specific problem"""
        problem_key = f"{problem_category}:{order_id}"
        self.attempts_by_problem[problem_key] = self.attempts_by_problem.get(problem_key, 0) + 1
        
        self.current_problem_category = problem_category
        self.current_order_id = order_id
    
    def get_attempts(self, problem_category: str, order_id: str) -> int:
        """Get number of attempts for a specific problem"""
        problem_key = f"{problem_category}:{order_id}"
        return self.attempts_by_problem.get(problem_key, 0)
    
    def is_stuck(self, problem_category: str, order_id: str) -> bool:
        """Check if stuck on this specific problem (3+ attempts)"""
        return self.get_attempts(problem_category, order_id) >= 3
    
    def reset_problem(self, problem_category: str, order_id: str):
        """Reset attempts for a specific problem (when resolved)"""
        problem_key = f"{problem_category}:{order_id}"
        if problem_key in self.attempts_by_problem:
            del self.attempts_by_problem[problem_key]
    
    def reset_all(self):
        """Clear all attempt tracking"""
        self.attempts_by_problem = {}
        self.current_order_id = None
        self.current_problem_category = None
    
    def get_summary(self) -> str:
        """Get a summary of current state"""
        return f"""
Agent State Summary:
- Problems tracked: {len(self.attempts_by_problem)}
- Current order: {self.current_order_id or 'None'}
- Current problem: {self.current_problem_category or 'None'}
- Attempts by problem: {self.attempts_by_problem}
"""