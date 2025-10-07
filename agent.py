# agent.py
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT
from functions import (
    check_order_status,
    check_tracking,
    initiate_refund,
    check_return_status,
    process_return_receipt,
    FUNCTION_DEFINITIONS
)
from database import db
from state import AgentState

# Load environment variables
load_dotenv()


class CustomerSupportAgent:
    def __init__(self):
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file!")
        
        self.client = OpenAI(api_key=api_key)
        self.conversation_history = []
        self.model = "gpt-4o-mini"  # Change to "gpt-4o" for better quality
        
        # Initialize state tracking
        self.state = AgentState()
        
        # Map function names to actual functions
        self.available_functions = {
            "check_order_status": check_order_status,
            "check_tracking": check_tracking,
            "initiate_refund": initiate_refund,
            "check_return_status": check_return_status
        }
    
    def _determine_problem_category(self, function_name: str) -> str:
        """Determine problem category from function name"""
        if function_name in ["initiate_refund", "check_return_status"]:
            return "refund_issue"
        elif function_name == "check_tracking":
            return "tracking_issue"
        elif function_name == "check_order_status":
            return "order_inquiry"
        else:
            return "general"
    
    def _extract_order_id(self, function_args: dict) -> str:
        """Extract order ID from function arguments"""
        # Direct order_id
        if "order_id" in function_args:
            return function_args["order_id"]
        
        # Extract from return_id (format: RET-12345)
        if "return_id" in function_args:
            return function_args["return_id"].replace("RET-", "")
        
        return "unknown"
    
    def chat(self, user_message: str) -> str:
        """
        Main chat method - handles conversation with function calling
        """
        print(f"\n{'='*60}")
        print(f"USER: {user_message}")
        print(f"{'='*60}")
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Determine temperature based on current problem state
        # We'll check after function call to see if we should adjust
        temperature = 0.7
        top_p = 0.9
        
        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *self.conversation_history
                ],
                functions=FUNCTION_DEFINITIONS,
                function_call="auto",
                temperature=temperature,
                top_p=top_p
            )
        except Exception as e:
            error_msg = f"Error calling OpenAI API: {str(e)}"
            print(f"❌ {error_msg}")
            return "I'm having trouble connecting right now. Please try again in a moment."
        
        message = response.choices[0].message
        
        # Check if the model wants to call a function
        if message.function_call:
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)
            
            print(f"\n🔧 CALLING FUNCTION: {function_name}")
            print(f"📋 ARGUMENTS: {json.dumps(function_args, indent=2)}")
            
            # Track attempt for this problem
            problem_category = self._determine_problem_category(function_name)
            order_id = self._extract_order_id(function_args)
            self.state.record_attempt(problem_category, order_id)
            
            # Check if stuck on this problem
            attempts = self.state.get_attempts(problem_category, order_id)
            if self.state.is_stuck(problem_category, order_id):
                print(f"⚠️  STUCK DETECTED: {attempts} attempts on {problem_category} for order {order_id}")
                print(f"🔥 Consider escalating or trying different approach")
            
            # Get the function from our mapping
            function_to_call = self.available_functions.get(function_name)
            
            if not function_to_call:
                print(f"❌ Unknown function: {function_name}")
                return "I encountered an error. Let me try a different approach."
            
            # Call the function
            try:
                function_response = function_to_call(**function_args)
                print(f"✅ FUNCTION RESULT: {json.dumps(function_response, indent=2)}")
                
                # If successful, reset attempts for this problem
                if function_response.get("success", True):
                    self.state.reset_problem(problem_category, order_id)
                    print(f"✨ Problem resolved! Reset attempts for {problem_category}:{order_id}")
                
            except Exception as e:
                print(f"❌ Function error: {str(e)}")
                function_response = {"error": f"Failed to execute {function_name}"}
            
            # Add function call and result to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": function_name,
                    "arguments": message.function_call.arguments
                }
            })
            
            self.conversation_history.append({
                "role": "function",
                "name": function_name,
                "content": json.dumps(function_response)
            })
            
            # Adjust temperature if stuck
            if self.state.is_stuck(problem_category, order_id):
                temperature = 1.0
                top_p = 0.85
                print(f"🔥 Increased temperature to {temperature} for next response")
            
            # Call the API again to get the final response
            try:
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        *self.conversation_history
                    ],
                    temperature=temperature,
                    top_p=top_p
                )
                
                final_message = second_response.choices[0].message.content
            except Exception as e:
                print(f"❌ Error getting final response: {str(e)}")
                final_message = "I found the information but had trouble formulating a response. Please try asking again."
            
            # Add assistant's final response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": final_message
            })
            
            return final_message
            
        else:
            # No function call - just a regular response
            assistant_message = message.content
            
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
    
    def reset(self):
        """Clear conversation history and state"""
        self.conversation_history = []
        self.state.reset_all()
        print("\n🔄 Conversation and state reset!\n")


def handle_admin_command(command: str):
    """Handle admin commands for simulation"""
    parts = command.split()
    
    if len(parts) < 2:
        print("❌ Invalid admin command")
        print("\nAvailable commands:")
        print("  /admin receive_return <return_id> <condition>")
        print("  /admin show_orders")
        print("  /admin show_returns")
        print("  /admin show_refunds")
        print("  /admin reset_database")
        return
    
    action = parts[1]
    
    if action == "receive_return":
        if len(parts) < 3:
            print("❌ Usage: /admin receive_return <return_id> <condition>")
            print("   Conditions: good, damaged, damaged_beyond_acceptable")
            return
        
        return_id = parts[2]
        condition = parts[3] if len(parts) > 3 else "good"
        
        result = process_return_receipt(return_id, condition)
        
        if result["success"]:
            print(f"\n✅ {result['message']}")
            print(f"   Return ID: {result['return_id']}")
            print(f"   Condition: {result['condition']}")
            print(f"   Status: {result['status']}")
            if result.get('refund_id'):
                print(f"   Refund ID: {result['refund_id']}")
        else:
            print(f"\n❌ {result.get('error', 'Failed to process return')}")
    
    elif action == "show_orders":
        print("\n📦 ALL ORDERS:")
        print(json.dumps(db.orders, indent=2))
    
    elif action == "show_returns":
        print("\n🔄 ALL RETURNS:")
        if db.returns:
            print(json.dumps(db.returns, indent=2))
        else:
            print("No returns in system")
    
    elif action == "show_refunds":
        print("\n💰 ALL REFUNDS:")
        if db.refunds:
            print(json.dumps(db.refunds, indent=2))
        else:
            print("No refunds in system")
    
    elif action == "reset_database":
        db.reset()
        print("\n✅ Database reset to initial state (10 sample orders)")
    
    else:
        print(f"❌ Unknown admin command: {action}")
        print("\nAvailable commands:")
        print("  /admin receive_return <return_id> <condition>")
        print("  /admin show_orders")
        print("  /admin show_returns")
        print("  /admin show_refunds")
        print("  /admin reset_database")


def main():
    """
    Main function to run the agent in terminal
    """
    print("\n" + "="*60)
    print("🤖 SHOPCO CUSTOMER SUPPORT AGENT v2.0")
    print("="*60)
    print("\nHello! I'm here to help with your orders, shipping, and returns.")
    print("\n📝 REGULAR COMMANDS:")
    print("  - Type your question normally")
    print("  - 'reset' - start a new conversation")
    print("  - 'quit' or 'exit' - end session")
    print("\n🔧 ADMIN COMMANDS (for simulation):")
    print("  - '/admin receive_return RET-12345 good' - mark return as received")
    print("  - '/admin show_orders' - view all orders")
    print("  - '/admin show_returns' - view all returns")
    print("  - '/admin show_refunds' - view all refunds")
    print("  - '/admin reset_database' - reset to initial state")
    print("\n💡 TIP: Try different order IDs (12345, 67890, 11111, etc.)")
    print("   - Some are 'processing' (can cancel directly)")
    print("   - Some are 'shipped' or 'delivered' (need return process)")
    print("\n" + "="*60 + "\n")
    
    agent = CustomerSupportAgent()
    
    while True:
        try:
            # Get user input
            user_input = input("YOU: ").strip()
            
            if not user_input:
                continue
            
            # Check for admin commands
            if user_input.startswith('/admin'):
                handle_admin_command(user_input)
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("\nAGENT: Thank you for contacting ShopCo! Have a great day! 👋\n")
                break
            
            if user_input.lower() == 'reset':
                agent.reset()
                continue
            
            # Get agent response
            response = agent.chat(user_input)
            
            # Print response
            print(f"\nAGENT: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋\n")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}\n")
            print("Please try again or type 'quit' to exit.\n")


if __name__ == "__main__":
    main()