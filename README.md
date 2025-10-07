# Customer Support AI Agent

A fully functional AI agent demonstrating core LLM concepts through practical implementation.

Built to understand how ChatGPT and similar AI systems actually work under the hood.

## 🎯 What This Teaches

- **Auto-regressive text generation** - How AI generates text one token at a time
- **Temperature and sampling** - What these parameters actually do (with math!)
- **Function calling** - How agents interact with external tools
- **State management** - Tracking conversation context and problem-solving progress
- **Agent orchestration** - Coordinating prompts, functions, and state

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Download the code**
   - Click the green "Code" button above
   - Click "Download ZIP"
   - Extract the ZIP file to your computer

2. **Install Python packages**

bash

pip install -r requirements.txt

3. **Set up your API key**

- Copy .env.example to a new file called .env
- Open .env and replace your-api-key-here with your actual OpenAI API key
- Save the file


4. **Run the agent**

bash   

python agent.py


## 💬 Try These Scenarios
The agent comes pre-loaded with 10 sample orders. Try these:

1. Cancel a Processing Order (Immediate Refund)

You: I want to cancel order 33333

The agent will check the status and process an immediate refund since it hasn't shipped yet.

2. Refund a Shipped Order (Return Process Required)

You: I need a refund for order 12345, the item arrived damaged

The agent will initiate a return process and provide a shipping label.

3. Simulate Warehouse Operations

You: /admin receive_return RET-12345 good

This simulates the warehouse receiving the returned item and triggers the refund.

4. Check Return Status

You: What's the status of return RET-12345?

**Available Test Orders**

Try these order IDs: 12345, 67890, 11111, 22222, 33333, 44444, 55555, 66666, 77777, 88888

Each has different statuses (processing, shipped, delivered) to test different scenarios.

## 📚 How It Works

The agent consists of 5 key components:
1. agent.py - The Orchestrator

Coordinates everything - manages conversation flow, calls OpenAI API, executes functions, tracks state.

2. prompts.py - The Instruction Manual

Defines the agent's personality, business rules, and guidelines through natural language.

3. functions.py - The Tools

The actual actions the agent can take: checking orders, processing refunds, handling returns.

4. database.py - The Memory

In-memory storage for orders, returns, and refunds. All functions read/write here.

5. state.py - The Attempt Tracker

Monitors if the agent is stuck on a problem and adjusts temperature accordingly.

## 🧠 Key Concepts Demonstrated

### Dynamic Temperature Adjustment

When the agent gets stuck on the same problem 3+ times, it increases temperature for more creative solutions:

python

if stuck_on_same_problem:

    temperature = 1.0  #More creative
else:

    temperature = 0.7  #Normal

### Smart Function Calling

The initiate_refund() function automatically determines the right approach:

Processing orders → Cancel and refund immediately

Shipped orders → Initiate return process first

### Granular State Tracking

Tracks attempts by problem_type:order_id to prevent false "stuck" detection:

refund_issue:12345 (3 attempts) → Stuck!

refund_issue:67890 (1 attempt) → Fine, different order

### Business Rules in Code

The AI is smart about language, but you define the business logic:

Shipped orders require returns before refunds

Refunds over $500 need supervisor approval

Return process takes 6-12 business days

## 🎓 What I Learned Building This

Prompts are 20% of the solution - you also need functions, state, and orchestration

Function calling isn't magic - You define what happens in your code

State management is harder than expected - conversation history ≠ problem-solving state

The AI part is actually easy - orchestration is the hard part

Temperature is math (logits / temperature), not just a "creativity dial"

## 🛠️ Admin Commands

For testing, you can simulate backend operations:

### Mark return as received (good condition)

bash

/admin receive_return RET-12345 good

### Mark return as received (damaged)

bash

/admin receive_return RET-12345 damaged_beyond_acceptable

### View all orders

bash

/admin show_orders

### View all returns

bash

/admin show_returns

### View all refunds

bash

/admin show_refunds

### Reset database to initial state

bash

/admin reset_database


## 📝 Architecture

User Input

    ↓
agent.py (Orchestrator)
   
    ├→ prompts.py (Instructions)
    ├→ state.py (Attempt tracking)   
    ↓
OpenAI API (GPT-4) 
    
    ↓
functions.py (Tools) 
   
    ↓
database.py (Data storage)
    
    ↓
Response to User


## ⚠️ Important Notes

This is for learning - Uses in-memory database that resets when you restart

API costs - Uses OpenAI API (costs ~$0.01-0.05 per conversation with gpt-4o-mini)

Not production-ready - No authentication, persistence, or error recovery for production use

## 🤝 Contributing
This is an educational project! Feedback and improvements welcome:

Open an issue for bugs or suggestions

Share what you learned

Build your own version and tell me about it!

## 📄 License
MIT License - see LICENSE file for details.

Free to use, modify, and learn from!

## 🙏 Acknowledgments
Built as a learning project to understand how LLMs work under the hood.

Inspired by curiosity about what happens behind the "Send" button in ChatGPT.

## Questions or feedback?
Open an issue 
