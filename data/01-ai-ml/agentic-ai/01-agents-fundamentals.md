# AI Agents: Fundamentals and Engineering

## 1. AI Agent Architecture

### 1.1 The Perception-Reasoning-Action Loop

An AI agent repeatedly perceives its environment, reasons about it, and acts upon it.

```mermaid
graph TD
    A["🌍 Environment"] -->|Perception<br/>observe state| B["👁️ Perception<br/>parse input<br/>gather state"]
    B -->|sensor data| C["🧠 Reasoning<br/>LLM thinks<br/>plans, decides"]
    C -->|decision| D["⚙️ Action<br/>call tools<br/>produce output"]
    D -->|execute| E["📊 Observe<br/>result of action"]
    E -->|feedback| A
    
    style A fill:#1a3a52
    style B fill:#2d5a7b
    style C fill:#4a8bc2
    style D fill:#2d5a7b
    style E fill:#1a3a52
```

#### Step-by-Step

1. **Perception Phase**: Agent reads raw input from environment (text, sensor data, API responses) and extracts meaningful state representation—cleaning, normalizing, and structuring the data.
2. **Context Building**: Retrieved state is added to the agent's internal memory alongside history, system prompt, and available tools to form the full context.
3. **LLM Reasoning**: Language model processes the context window and generates reasoning output that may include thoughts, analysis, and a decision about what action to take.
4. **Action Selection**: Agent parses LLM output to identify the chosen action (tool call, API invocation, or final answer) and extracts required parameters.
5. **Execution**: Selected action is executed in the real environment—returning results that are then observed by the agent.
6. **Feedback Loop**: Observation is added to memory, loop returns to perception for the next iteration, refining decisions based on previous results.

#### Code Example

```python
# Complete perception-reasoning-action loop
import json
from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class AgentStep:
    observation: Optional[str] = None
    thought: str = ""
    action: str = ""
    action_input: Dict = None
    observation_result: str = ""

class PerceptionReasoningActionLoop:
    def __init__(self, llm_callable, tools: Dict[str, callable]):
        self.llm = llm_callable  # LLM inference function
        self.tools = tools  # Available tool functions
        self.memory = []  # Perception history
        self.max_iterations = 10

    def perceive(self, raw_input: str) -> Dict[str, Any]:
        """Step 1: Parse and structure input from environment."""
        # Clean and normalize input
        cleaned = raw_input.strip()
        # Extract entities, intent, context
        perception = {
            "raw_input": cleaned,
            "length": len(cleaned),
            "has_question": "?" in cleaned,
            "timestamp": __import__("time").time()
        }
        self.memory.append({"role": "user", "content": cleaned})
        return perception

    def reason(self) -> str:
        """Step 2-3: Use LLM to generate reasoning and decision."""
        # Build context from memory
        system_prompt = "You are a helpful agent. Respond with Thought, then Action."
        messages = [{"role": "system", "content": system_prompt}] + self.memory
        
        # Call LLM (step 3)
        reasoning = self.llm(messages)
        return reasoning

    def act(self, reasoning: str) -> AgentStep:
        """Step 4: Parse reasoning and select action."""
        step = AgentStep(thought=reasoning)
        
        # Extract action from LLM output
        if "Action:" in reasoning:
            action_part = reasoning.split("Action:")[-1].strip()
            if "(" in action_part and ")" in action_part:
                tool_name = action_part.split("(")[0].strip()
                args_str = action_part.split("(")[1].rstrip(")")
                
                step.action = tool_name
                try:
                    step.action_input = json.loads("{" + args_str + "}")
                except json.JSONDecodeError:
                    step.action_input = {"query": args_str}
        return step

    def execute_action(self, step: AgentStep) -> str:
        """Step 5: Execute action in environment."""
        if step.action in self.tools:
            try:
                result = self.tools[step.action](**step.action_input)
                step.observation_result = str(result)
            except Exception as e:
                step.observation_result = f"Tool error: {str(e)}"
        else:
            step.observation_result = f"Unknown tool: {step.action}"
        return step.observation_result

    def loop(self, user_input: str) -> str:
        """Complete PRA loop: perceive -> reason -> act -> observe -> repeat."""
        perception = self.perceive(user_input)  # Step 1
        
        for iteration in range(self.max_iterations):
            reasoning = self.reason()  # Step 2-3
            step = self.act(reasoning)  # Step 4
            
            if "Final Answer:" in reasoning:
                return reasoning.split("Final Answer:")[-1].strip()
            
            observation = self.execute_action(step)  # Step 5
            self.memory.append({"role": "assistant", "content": reasoning})
            self.memory.append({"role": "user", "content": f"Observation: {observation}"})
        
        return "Max iterations reached"

# Usage example
def search_tool(query: str) -> str:
    return f"Found information about: {query}"

def calculator_tool(expression: str) -> str:
    return f"Result: {eval(expression)}"

agent = PerceptionReasoningActionLoop(
    llm_callable=lambda msgs: "Thought: I should search.\nAction: search_tool(\"AI agents\")",
    tools={"search_tool": search_tool, "calculator_tool": calculator_tool}
)

result = agent.loop("What is the capital of France?")
print(result)
```

#### Real-World Scenario

At a customer service company, a support agent receives 50+ tickets per hour. When a customer submits a ticket ("My order hasn't shipped in 3 days"), the system: perceives the complaint via NLP extraction, reasons about whether to apologize+search knowledge base or escalate, acts by querying the order database and ticket system, observes the order status (delayed due to inventory), and loops to generate a personalized response. The feedback mechanism logs customer sentiment to improve future agent reasoning thresholds.

#### Diagram

```mermaid
graph LR
    A["User Input"] --> B["Perception<br/>NLP Parse"]
    B --> C["Memory<br/>History+Context"]
    C --> D["LLM<br/>Reason"]
    D --> E{"Parse<br/>Output"}
    E -->|Action| F["Execute<br/>Tool"]
    E -->|Final| G["Return"]
    F --> H["Observation"]
    H --> I["Add Memory"]
    I --> D
    G --> J["Response"]
```

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json

@dataclass
class Observation:
    content: str
    role: str
    metadata: Optional[Dict] = None

@dataclass
class Action:
    name: str
    args: Dict[str, Any]
    result: Optional[Any] = None

class BaseAgent(ABC):
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.memory: List[Observation] = []
        self.state: Dict = {}

    @abstractmethod
    def perceive(self, observation: Observation):
        pass

    @abstractmethod
    def reason(self) -> str:
        pass

    @abstractmethod
    def act(self, decision: str) -> Action:
        pass

    def step(self, observation: Observation):
        self.perceive(observation)
        decision = self.reason()
        action = self.act(decision)
        return action


class SimpleReActAgent(BaseAgent):
    def __init__(self, system_prompt: str, llm_callable):
        super().__init__(system_prompt)
        self.llm = llm_callable
        self.max_steps = 10

    def perceive(self, observation: Observation):
        self.memory.append(observation)

    def reason(self) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        for obs in self.memory:
            messages.append({"role": obs.role, "content": obs.content})
        response = self.llm(messages)
        return response

    def act(self, decision: str) -> Action:
        if "Action:" in decision:
            action_line = decision.split("Action:")[1].strip()
            tool_name = action_line.split("(")[0]
            args_str = action_line.split("(")[1].rstrip(")")
            args = json.loads(args_str)
            return Action(name=tool_name, args=args)
        else:
            return Action(name="final_answer", args={"content": decision})
```

### 1.2 Agent State Machine

```python
from enum import Enum

class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    COMPLETED = "completed"
    ERROR = "error"

class StatefulAgent:
    def __init__(self, system_prompt):
        self.state = AgentState.IDLE
        self.system_prompt = system_prompt
        self.conversation_history = []
        self.current_plan = []

    def transition(self, new_state: AgentState):
        print(f"State: {self.state.value} -> {new_state.value}")
        self.state = new_state

    def run(self, task: str) -> str:
        self.transition(AgentState.THINKING)
        plan = self.create_plan(task)
        self.current_plan = plan
        for step in plan:
            self.transition(AgentState.ACTING)
            result = self.execute_step(step)
            self.transition(AgentState.OBSERVING)
            self.process_result(result)
        self.transition(AgentState.COMPLETED)
        return self.summarize()

    def create_plan(self, task):
        prompt = f"Break this task into sequential steps:\n{task}"
        response = self.llm(prompt)
        steps = self.parse_steps(response)
        return steps
```

#### Step-by-Step

1. **State Definition**: Create enumeration of valid states (IDLE, THINKING, ACTING, OBSERVING, COMPLETED, ERROR) and track current state in the agent instance.
2. **Initial Transition**: Move from IDLE to THINKING when a new task arrives, signaling the agent is analyzing the problem.
3. **Planning Phase**: LLM generates a decomposed plan (list of sub-steps) and stores it in memory for execution tracking.
4. **Action-Observation Loop**: For each step in the plan, agent transitions to ACTING (executes tool/function), then OBSERVING (processes result), repeating until plan is exhausted.
5. **Error Handling**: If any step fails, transition to ERROR state, log details, attempt recovery or escalation based on policy.
6. **Completion**: Once all steps succeed, transition to COMPLETED state and generate final summary from accumulated observations.

#### Code Example

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

class AgentState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    ACTING = "acting"
    OBSERVING = "observing"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class StateTransition:
    from_state: AgentState
    to_state: AgentState
    timestamp: float
    reason: str

class StatefulAgent:
    def __init__(self, system_prompt: str, max_retries: int = 3):
        self.state = AgentState.IDLE
        self.system_prompt = system_prompt
        self.history = []
        self.transitions: List[StateTransition] = []
        self.max_retries = max_retries
        self.retry_count = 0

    def transition(self, new_state: AgentState, reason: str = ""):
        """Execute state transition with logging."""
        if self._is_valid_transition(self.state, new_state):
            transition = StateTransition(
                from_state=self.state,
                to_state=new_state,
                timestamp=datetime.now().timestamp(),
                reason=reason
            )
            self.transitions.append(transition)
            old_state = self.state
            self.state = new_state
            print(f"[{old_state.value} -> {new_state.value}] {reason}")
            return True
        return False

    def _is_valid_transition(self, from_state: AgentState, to_state: AgentState) -> bool:
        """Define allowed state transitions."""
        valid_transitions = {
            AgentState.IDLE: [AgentState.PLANNING],
            AgentState.PLANNING: [AgentState.ACTING, AgentState.FAILED],
            AgentState.ACTING: [AgentState.OBSERVING, AgentState.RECOVERING],
            AgentState.OBSERVING: [AgentState.ACTING, AgentState.COMPLETED, AgentState.FAILED],
            AgentState.RECOVERING: [AgentState.ACTING, AgentState.FAILED],
            AgentState.COMPLETED: [AgentState.IDLE],
            AgentState.FAILED: [AgentState.RECOVERING, AgentState.IDLE],
        }
        return to_state in valid_transitions.get(from_state, [])

    def run(self, task: str) -> dict:
        """Complete state machine execution."""
        self.transition(AgentState.PLANNING, f"Task: {task[:30]}...")
        
        try:
            plan = self._create_plan(task)
            results = []
            
            for step_idx, step in enumerate(plan):
                self.transition(AgentState.ACTING, f"Step {step_idx + 1}/{len(plan)}")
                result = self._execute_step(step)
                
                self.transition(AgentState.OBSERVING, f"Analyzing result")
                processed = self._process_result(result)
                results.append(processed)
                
                if not processed.get("success", False):
                    self.retry_count += 1
                    if self.retry_count < self.max_retries:
                        self.transition(AgentState.RECOVERING, f"Retry {self.retry_count}")
                        result = self._execute_step(step)  # Retry
                    else:
                        raise Exception(f"Step {step_idx} failed after retries")
            
            self.transition(AgentState.COMPLETED, "All steps succeeded")
            return {"status": "success", "results": results}
            
        except Exception as e:
            self.transition(AgentState.FAILED, f"Error: {str(e)}")
            return {"status": "failed", "error": str(e)}

    def _create_plan(self, task: str) -> List[str]:
        """Generate decomposed plan."""
        prompt = f"Break this task into 3-5 sequential steps:\n{task}"
        # In real code, call LLM here
        return [f"Step {i+1}" for i in range(3)]

    def _execute_step(self, step: str) -> dict:
        """Execute single step (simulated)."""
        return {"step": step, "output": f"Result of {step}"}

    def _process_result(self, result: dict) -> dict:
        """Process and validate result."""
        return {"success": True, "data": result}

# Usage
agent = StatefulAgent("You are a helpful agent")
result = agent.run("Find the weather and book a flight")
print(result)
```

#### Real-World Scenario

A data pipeline agent ingests 10GB of customer transaction data. It transitions IDLE→PLANNING (breaks task: validation→deduplication→enrichment→loading), then cycles through ACTING→OBSERVING for each step. When validation fails on 2% of records (row count mismatch), it transitions to RECOVERING, retries with relaxed schema validation. After 3 retries still failing, it transitions FAILED and escalates to a data engineer via Slack, preventing downstream corruption.

#### Diagram

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> PLANNING: New task
    PLANNING --> ACTING: Generate plan
    ACTING --> OBSERVING: Execute step
    OBSERVING --> ACTING: Continue
    OBSERVING --> COMPLETED: All done
    OBSERVING --> RECOVERING: Failure detected
    ACTING --> RECOVERING: Execution error
    RECOVERING --> ACTING: Retry
    RECOVERING --> FAILED: Max retries
    FAILED --> IDLE: Reset
    COMPLETED --> IDLE: Reset
```

## 2. ReAct Pattern

### 2.1 Standard ReAct

ReAct interleaves reasoning traces (Thought) with actions and observations:

```
Thought: I need to find the current weather in London.
Action: search(query="London weather 2026")
Observation: London is currently 18C and partly cloudy.

Thought: The user asked if they need an umbrella.
Action: search(query="London weather forecast today rain probability")
Observation: 30% chance of rain in the afternoon.

Thought: 30% chance is moderate. Recommend umbrella.
Final Answer: You should bring an umbrella.
```

#### Step-by-Step

1. **Thought Generation**: LLM analyzes the user query and current observations, generating reasoning about what information is needed or what decision should be made.
2. **Action Selection**: Based on reasoning, LLM selects an appropriate tool (search, calculate, API call) and formats the action with parameters.
3. **Tool Execution**: Selected action is executed synchronously in real environment, returning concrete results (search findings, calculation output, API response).
4. **Observation Recording**: Tool output is captured as an observation and added to the reasoning chain to provide ground truth context.
5. **Loop Decision**: Agent determines whether to continue (generate new Thought) or halt with Final Answer based on whether the question is answered.
6. **Answer Generation**: When sufficient information is gathered, LLM generates Final Answer by synthesizing all observations into a coherent response.

#### Code Example

```python
import json
import re
from typing import Dict, List, Callable, Optional

class Tool:
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

    def execute(self, **kwargs) -> str:
        try:
            result = self.func(**kwargs)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"

class ReActAgent:
    def __init__(self, llm_callable: Callable, tools: List[Tool]):
        self.llm = llm_callable
        self.tools = {t.name: t for t in tools}
        self.max_iterations = 10
        self.reasoning_trace = []

    def run(self, question: str) -> str:
        """Execute ReAct loop: Thought -> Action -> Observation -> repeat."""
        self.reasoning_trace = [f"Question: {question}\n"]
        
        for iteration in range(self.max_iterations):
            # Step 1: Generate thought
            prompt = self._build_prompt()
            response = self.llm(prompt)
            
            # Check for final answer (Step 6)
            if "Final Answer:" in response:
                final = response.split("Final Answer:")[-1].strip()
                self.reasoning_trace.append(f"Final Answer: {final}")
                return final
            
            # Step 2: Extract thought
            thought = self._extract_thought(response)
            if thought:
                self.reasoning_trace.append(f"Thought: {thought}")
            
            # Step 3-4: Parse action and execute
            action_info = self._parse_action(response)
            if action_info:
                tool_name, args = action_info
                observation = self._execute_action(tool_name, args)  # Steps 3-4
                self.reasoning_trace.append(f"Action: {tool_name}({json.dumps(args)})")
                self.reasoning_trace.append(f"Observation: {observation}")
            else:
                break
        
        return "Max iterations reached without answer"

    def _build_prompt(self) -> str:
        """Build prompt with trace history."""
        system = """You are a helpful reasoning agent.
For each response:
1. Provide a Thought analyzing the situation
2. Choose an Action from available tools, or
3. Provide Final Answer if you have enough information

Format:
Thought: <your reasoning>
Action: <tool_name>(<json_args>)
Or: Final Answer: <your answer>

Available tools: """ + ", ".join(self.tools.keys())
        
        trace_str = "\n".join(self.reasoning_trace)
        return f"{system}\n\n{trace_str}\nThought:"

    def _extract_thought(self, response: str) -> str:
        """Extract thought from LLM response."""
        if "Thought:" in response:
            thought = response.split("Thought:")[1]
            if "Action:" in thought:
                thought = thought.split("Action:")[0]
            return thought.strip()
        return ""

    def _parse_action(self, response: str) -> Optional[tuple]:
        """Parse action from LLM response."""
        match = re.search(r'Action:\s*(\w+)\s*\((.*?)\)', response, re.DOTALL)
        if not match:
            return None
        
        tool_name = match.group(1)
        args_str = match.group(2).strip()
        
        try:
            args = json.loads(args_str)
        except json.JSONDecodeError:
            # Try to parse as key=value pairs
            args = {}
            for pair in args_str.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    args[k.strip()] = v.strip().strip('"')
        
        return tool_name, args

    def _execute_action(self, tool_name: str, args: Dict) -> str:
        """Execute tool and return observation."""
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"
        
        tool = self.tools[tool_name]
        return tool.execute(**args)

# Example tools
def web_search(query: str) -> str:
    """Simulate web search."""
    return f"Found articles about: {query}"

def get_weather(city: str) -> str:
    """Simulate weather API."""
    return f"Weather in {city}: 18C, partly cloudy"

def calculator(expression: str) -> str:
    """Simple calculator."""
    return f"Result: {eval(expression)}"

# Setup agent
tools = [
    Tool("search", "Search the web", web_search),
    Tool("weather", "Get weather for a city", get_weather),
    Tool("calc", "Evaluate math expressions", calculator),
]

agent = ReActAgent(
    llm_callable=lambda p: "Thought: I should search for more info\nAction: search(query=\"umbrella\")",
    tools=tools
)

answer = agent.run("Should I bring an umbrella to London?")
print(f"Answer: {answer}")
```

#### Real-World Scenario

A financial advisor chatbot receives a query: "What's my account balance and should I invest in tech stocks?" The ReAct loop: Thought 1 determines it needs account data, executes check_balance tool (gets $50,000), Thought 2 recognizes it needs market data, executes get_tech_index tool (gets current performance), Thought 3 synthesizes both: balance is adequate, tech sector is up 12% this quarter but volatile. Final Answer: "Your balance is solid for diversified investment; recommend 40% tech allocation." This reasoning chain is logged and explainable to the user.

#### Diagram

```mermaid
graph TD
    Q["User Question"] --> T1["Thought: Plan"]
    T1 --> A1["Action: Tool Call"]
    A1 --> O1["Observation: Result"]
    O1 --> T2{"More Info<br/>Needed?"}
    T2 -->|Yes| T2a["Thought: Refine"]
    T2a --> A2["Action: Tool Call"]
    A2 --> O2["Observation: Result"]
    O2 --> T2
    T2 -->|No| FA["Final Answer"]
    FA --> R["Return to User"]
```

```python
class ReActAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = {t.name: t for t in tools}
        self.max_iterations = 15

    def run(self, question: str):
        thoughts = []
        actions = []
        for step in range(self.max_iterations):
            prompt = self.build_react_prompt(question, thoughts, actions)
            response = self.llm(prompt)
            if "Final Answer:" in response:
                return response.split("Final Answer:")[1].strip()
            thought = self.extract_thought(response)
            if thought:
                thoughts.append(thought)
            action_info = self.parse_action(response)
            if action_info:
                tool_name, args = action_info
                actions.append({"action": tool_name, "args": args})
                result = self.execute_tool(tool_name, args)
                actions[-1]["result"] = result
        return "Max iterations reached."

    def build_react_prompt(self, question, thoughts, actions):
        prompt = f"Question: {question}\n\n"
        for t, a in zip(thoughts, actions):
            prompt += f"Thought: {t}\n"
            if a.get("action"):
                prompt += f"Action: {a['action']}({json.dumps(a['args'])})\n"
                prompt += f"Observation: {a.get('result', '')}\n"
        prompt += "Thought: "
        return prompt

    def extract_thought(self, response):
        if "Thought:" in response:
            return response.split("Thought:")[1].split("Action:")[0].strip() if "Action:" in response else ""
        return None

    def parse_action(self, response):
        import re
        match = re.search(r'Action:\s*(\w+)\(([^)]*)\)', response)
        if match:
            tool_name = match.group(1)
            args_str = match.group(2)
            if args_str.strip():
                args = json.loads("{" + args_str + "}")
            else:
                args = {}
            return tool_name, args
        return None

    def execute_tool(self, name, args):
        if name in self.tools:
            return self.tools[name].execute(**args)
        return f"Error: Unknown tool '{name}'"
```

## 3. Tool Calling

### 3.1 Tool Definition

```python
from typing import Callable, get_type_hints
import inspect

class Tool:
    def __init__(self, name: str, description: str, fn: Callable):
        self.name = name
        self.description = description
        self.fn = fn
        self.parameters = self.extract_parameters()

    def extract_parameters(self):
        sig = inspect.signature(self.fn)
        hints = get_type_hints(self.fn)
        properties = {}
        required = []
        for name, param in sig.parameters.items():
            properties[name] = {
                "type": self.pytype_to_json(hints.get(name, str)),
                "description": f"Parameter {name}"
            }
            if param.default is inspect.Parameter.empty:
                required.append(name)
        return {"type": "object", "properties": properties, "required": required}

    def pytype_to_json(self, t):
        mapping = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}
        return mapping.get(t, "string")

    def to_openai_format(self):
        return {"type": "function", "function": {"name": self.name, "description": self.description, "parameters": self.parameters}}

    def execute(self, **kwargs):
        return self.fn(**kwargs)
```

#### Step-by-Step

1. **Function Introspection**: Use Python's `inspect` module to read function signature, extracting parameter names, types, and default values.
2. **Type Mapping**: Convert Python type hints to JSON Schema types (str→string, int→integer, float→number, etc.) for LLM compatibility.
3. **Schema Generation**: Build OpenAI-compatible tool schema with function name, description, and parameter JSON Schema (properties and required fields).
4. **Validation Setup**: Mark parameters without defaults as required, allowing LLM to understand which arguments must be provided.
5. **Format Conversion**: Package the schema in OpenAI tool-calling format for API transmission.
6. **Execution Wrapper**: Implement execute method that safely calls the underlying function with validated kwargs and handles errors.

#### Code Example

```python
import inspect
from typing import Callable, get_type_hints, Optional, Any, Dict, List
import json

class ToolParameter:
    def __init__(self, name: str, param_type: str, description: str, required: bool):
        self.name = name
        self.param_type = param_type
        self.description = description
        self.required = required

class Tool:
    """Tool definition with schema generation and execution."""
    
    def __init__(self, name: str, description: str, fn: Callable, examples: List[str] = None):
        self.name = name
        self.description = description
        self.fn = fn
        self.examples = examples or []
        self.call_count = 0
        self.last_error = None
        self.parameters = self._extract_parameters()

    def _extract_parameters(self) -> Dict[str, Any]:
        """Extract parameters from function signature."""
        sig = inspect.signature(self.fn)
        try:
            hints = get_type_hints(self.fn)
        except:
            hints = {}
        
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            # Skip 'self' in methods
            if param_name == 'self':
                continue
            
            # Get type hint or default to str
            param_type = hints.get(param_name, str)
            json_type = self._python_type_to_json(param_type)
            
            # Extract docstring-based description if available
            description = f"Parameter: {param_name}"
            if self.fn.__doc__ and param_name in self.fn.__doc__:
                # Parse from docstring (simplified)
                description = param_name
            
            properties[param_name] = {
                "type": json_type,
                "description": description
            }
            
            # Check if required (no default value)
            if param.default is inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    def _python_type_to_json(self, py_type: Any) -> str:
        """Convert Python type to JSON Schema type."""
        mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            List: "array",
            Dict: "object",
            Optional[str]: "string",
        }
        
        # Handle Optional types
        if hasattr(py_type, '__origin__'):
            origin = py_type.__origin__
            if origin in mapping:
                return mapping[origin]
        
        return mapping.get(py_type, "string")

    def to_openai_format(self) -> Dict[str, Any]:
        """Format for OpenAI API tool calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def to_claude_format(self) -> Dict[str, Any]:
        """Format for Claude API."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters["properties"],
                "required": self.parameters["required"]
            }
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool with error handling."""
        self.call_count += 1
        try:
            result = self.fn(**kwargs)
            return {
                "success": True,
                "result": result,
                "call_count": self.call_count
            }
        except TypeError as e:
            # Missing required parameter
            self.last_error = f"Invalid arguments: {str(e)}"
            return {
                "success": False,
                "error": self.last_error,
                "expected_params": self.parameters["required"]
            }
        except Exception as e:
            self.last_error = str(e)
            return {
                "success": False,
                "error": self.last_error,
                "error_type": type(e).__name__
            }

    def validate_args(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate arguments before execution."""
        required = self.parameters.get("required", [])
        
        # Check all required params present
        for param in required:
            if param not in kwargs:
                return False, f"Missing required parameter: {param}"
        
        # Check no unexpected params
        valid_params = set(self.parameters["properties"].keys())
        provided_params = set(kwargs.keys())
        unexpected = provided_params - valid_params
        if unexpected:
            return False, f"Unexpected parameters: {unexpected}"
        
        return True, None

# Example tools
def search_documents(query: str, max_results: int = 5) -> List[Dict]:
    """Search documents by keyword query."""
    return [{"id": 1, "title": f"Result for {query}"}] * min(max_results, 5)

def calculate_sum(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b

def get_user_info(user_id: int) -> Dict[str, Any]:
    """Get user information by ID."""
    return {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}

# Create tool instances
tools = [
    Tool("search", "Search documents with a keyword query", search_documents),
    Tool("add", "Add two numbers together", calculate_sum),
    Tool("get_user", "Retrieve user details by ID", get_user_info),
]

# Test tool
search_tool = tools[0]
print(f"Tool: {search_tool.name}")
print(f"OpenAI Format: {json.dumps(search_tool.to_openai_format(), indent=2)}")
print(f"Execution: {search_tool.execute(query='python agents', max_results=3)}")
```

#### Real-World Scenario

A customer support platform defines tools: `query_order_history(customer_id: int)`, `send_email(email: str, subject: str, body: str)`, `create_refund(order_id: int, amount: float)`. When an agent receives a refund request, the system auto-generates JSON schemas for each tool, passes them to Claude, and Claude selects the appropriate tool chain: query_order_history → inspect order amount → create_refund → send_email confirmation. If Claude tries to call `create_refund` with non-integer order_id, the validation catches it and returns an error asking Claude to fix the argument types.

#### Diagram

```mermaid
graph LR
    A["Python Function"] --> B["inspect.signature<br/>Extract params"]
    B --> C["get_type_hints<br/>Get types"]
    C --> D["Map to JSON Schema<br/>str→string"]
    D --> E["Build parameters<br/>object"]
    E --> F["OpenAI Format<br/>or Claude Format"]
    F --> G["Send to LLM"]
    G --> H["LLM calls tool<br/>with arguments"]
    H --> I["execute(**kwargs)"]
    I --> J["Return result"]
```


def search_web(query: str) -> str:
    return f"Search results for '{query}': [simulated results]"

def calculate(expression: str) -> str:
    try:
        return f"Result: {eval(expression)}"
    except Exception as e:
        return f"Error: {e}"

def get_weather(city: str, units: str = "celsius") -> str:
    return f"Weather in {city}: 22 degrees, partly cloudy"

def send_email(to: str, subject: str, body: str) -> str:
    return f"Email sent to {to} with subject '{subject}'"

tools = [
    Tool("search_web", "Search the web for current information", search_web),
    Tool("calculate", "Evaluate mathematical expressions", calculate),
    Tool("get_weather", "Get weather for a city", get_weather),
    Tool("send_email", "Send an email message", send_email),
]
```

### 3.2 Function Calling with LLM APIs

```python
class ToolExecutor:
    def __init__(self, tools: List[Tool]):
        self.tools = {t.name: t for t in tools}

    def execute(self, tool_name: str, arguments: Dict) -> str:
        if tool_name not in self.tools:
            return f"Error: tool '{tool_name}' not found"
        tool = self.tools[tool_name]
        try:
            return str(tool.execute(**arguments))
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"


class LLMWithTools:
    def __init__(self, llm_client, tools: List[Tool]):
        self.client = llm_client
        self.tool_executor = ToolExecutor(tools)
        self.tool_defs = [t.to_openai_format() for t in tools]

    def run(self, messages: List[Dict]) -> str:
        response = self.client.chat(messages=messages, tools=self.tool_defs, tool_choice="auto")
        if response.choices[0].finish_reason == "tool_calls":
            tool_call = response.choices[0].message.tool_calls[0]
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            result = self.tool_executor.execute(tool_name, arguments)
            messages.append(response.choices[0].message)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
            return self.run(messages)
        return response.choices[0].message.content
```

## 4. Memory Systems

### 4.1 Short-Term Memory (Context Window)

#### Step-by-Step

1. **Message Recording**: Each agent interaction (user input, assistant response, tool output) is appended to the message list with role and content.
2. **Token Estimation**: Periodically estimate total tokens in memory (rough: 1 token ≈ 3-4 characters) to track approaching context limits.
3. **Overflow Detection**: When token count exceeds max_tokens threshold, trigger trimming to free space.
4. **FIFO Removal**: Remove oldest non-system messages first to preserve recent context critical for coherent reasoning.
5. **Repeat Until Fit**: Continue removing oldest messages until total tokens fall below threshold.
6. **Context Retrieval**: Return messages in original or reverse order (recent-first) depending on use case (prepend recent for focus vs. chronological history).

#### Code Example

```python
from collections import deque
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Message:
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tokens: Optional[int] = None
    metadata: Optional[Dict] = None

class ShortTermMemory:
    """Sliding window memory with token-based trimming."""
    
    def __init__(self, max_tokens: int = 4096, min_messages: int = 2):
        self.max_tokens = max_tokens
        self.min_messages = min_messages  # Keep at least system + 1 other
        self.messages: List[Message] = []
        self.total_tokens = 0

    def add(self, role: str, content: str, metadata: Dict = None):
        """Add message and auto-trim if needed."""
        tokens = self._estimate_tokens(content)
        msg = Message(role=role, content=content, tokens=tokens, metadata=metadata)
        self.messages.append(msg)
        self.total_tokens += tokens
        
        # Trim if over limit
        if self.total_tokens > self.max_tokens:
            self._trim()

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation: 1 token ≈ 3-4 chars."""
        return max(1, len(text) // 4)

    def _trim(self):
        """Remove oldest non-system messages until under limit."""
        while self.total_tokens > self.max_tokens and len(self.messages) > self.min_messages:
            # Find first non-system message
            for i, msg in enumerate(self.messages):
                if msg.role != "system":
                    removed = self.messages.pop(i)
                    self.total_tokens -= removed.tokens
                    print(f"Trimmed: {removed.role} message ({removed.tokens} tokens)")
                    break

    def get_context(self, recent_first: bool = False) -> List[Dict]:
        """Return messages for LLM context."""
        msgs = [(m.role, m.content) for m in self.messages]
        if recent_first:
            msgs = list(reversed(msgs))
        return [{"role": r, "content": c} for r, c in msgs]

    def get_summary(self) -> Dict:
        """Return memory statistics."""
        return {
            "total_messages": len(self.messages),
            "total_tokens": self.total_tokens,
            "utilization": f"{self.total_tokens / self.max_tokens * 100:.1f}%",
            "roles": {r: sum(1 for m in self.messages if m.role == r) for r in set(m.role for m in self.messages)}
        }

    def clear(self):
        """Reset memory."""
        self.messages = []
        self.total_tokens = 0

# Test
memory = ShortTermMemory(max_tokens=200)
memory.add("system", "You are a helpful assistant.")
memory.add("user", "Tell me about climate change and its impacts on ecosystems around the world.")
memory.add("assistant", "Climate change is causing significant warming...")
memory.add("user", "What about polar regions?")
print(memory.get_summary())
```

#### Real-World Scenario

A chat application's agent handles customer support tickets. Each conversation appends: user message, agent thought process, tool calls (API queries), and responses. After 50 exchanges (~15KB), the context window (4K tokens) fills. The system auto-trims: removes oldest user message pair (5 exchanges from hour 1, 50 tokens), restoring capacity. Recent conversation (last hour) remains intact for coherence. When customer asks "What did you recommend earlier?", the agent only sees last 10 exchanges, but the trimmed context preserved enough for continuity.

#### Diagram

```mermaid
graph LR
    A["Add Message"] --> B["Estimate Tokens"]
    B --> C["Append to List"]
    C --> D{"Total Tokens<br/>Over Limit?"}
    D -->|No| E["Keep All"]
    D -->|Yes| F["Trim Loop"]
    F --> G["Find Oldest<br/>Non-System"]
    G --> H["Remove"]
    H --> I{"Still Over?"}
    I -->|Yes| F
    I -->|No| J["Done"]
    E --> K["Return Context"]
    J --> K
```

```python
class ShortTermMemory:
    def __init__(self, max_tokens: int = 4096):
        self.max_tokens = max_tokens
        self.messages: List[Dict] = []

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self.trim()

    def trim(self):
        while self.estimate_tokens() > self.max_tokens:
            for i, msg in enumerate(self.messages):
                if msg["role"] in ("user", "assistant"):
                    self.messages.pop(i)
                    break

    def estimate_tokens(self, text: str = None):
        if text is None:
            return sum(len(m["content"]) // 3 for m in self.messages)
        return len(text) // 3

    def get_context(self, recent_first: bool = False):
        if recent_first:
            return list(reversed(self.messages))
        return self.messages


class SlidingWindowMemory:
    def __init__(self, max_recent: int = 10):
        self.max_recent = max_recent
        self.recent_messages = []
        self.summary = ""

    def add(self, message):
        self.recent_messages.append(message)
        if len(self.recent_messages) > self.max_recent * 2:
            self.compress()

    def compress(self):
        older = self.recent_messages[:-self.max_recent]
        summary_prompt = f"Summarize these messages:\n{json.dumps(older)}"
        new_summary = self.llm(summary_prompt)
        self.summary = new_summary if not self.summary else f"{self.summary}\n{new_summary}"
        self.recent_messages = self.recent_messages[-self.max_recent:]
```

### 4.2 Long-Term Memory (RAG / Vector Store)

```python
class VectorMemory:
    def __init__(self, embedding_fn, top_k: int = 5):
        self.embedding_fn = embedding_fn
        self.top_k = top_k
        self.vectors = {}
        self.texts = {}
        self.metadata = {}

    def add(self, text: str, metadata: Dict = None):
        doc_id = str(hash(text))
        if doc_id not in self.vectors:
            self.vectors[doc_id] = self.embedding_fn(text)
            self.texts[doc_id] = text
            self.metadata[doc_id] = metadata or {}

    def search(self, query: str, top_k: int = None):
        k = top_k or self.top_k
        query_emb = self.embedding_fn(query)
        similarities = []
        for doc_id, emb in self.vectors.items():
            sim = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))
            similarities.append((doc_id, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = []
        for doc_id, sim in similarities[:k]:
            results.append({"text": self.texts[doc_id], "score": sim, "metadata": self.metadata[doc_id]})
        return results

    def consolidate(self, agent_llm):
        all_texts = list(self.texts.values())
        if len(all_texts) > 100:
            chunk = "\n".join(all_texts[:50])
            summary = agent_llm(f"Summarize these memories:\n{chunk}")
            for doc_id in list(self.texts.keys())[:50]:
                del self.vectors[doc_id]
                del self.texts[doc_id]
                del self.metadata[doc_id]
            self.add(summary, {"type": "summary"})
```

### 4.3 Episodic Memory

```python
import time
from collections import Counter

class EpisodicMemory:
    def __init__(self):
        self.episodes = []

    def record_episode(self, state, action, reward, next_state):
        self.episodes.append({
            "state": state, "action": action, "reward": reward,
            "next_state": next_state, "timestamp": time.time()
        })

    def retrieve_similar_episodes(self, current_state, k=3):
        scored = []
        for ep in self.episodes:
            similarity = self.state_similarity(current_state, ep["state"])
            scored.append((similarity, ep))
        scored.sort(reverse=True)
        return [ep for _, ep in scored[:k]]

    def state_similarity(self, s1, s2):
        if isinstance(s1, str) and isinstance(s2, str):
            s1_set = set(s1.lower().split())
            s2_set = set(s2.lower().split())
            intersection = s1_set & s2_set
            union = s1_set | s2_set
            return len(intersection) / len(union) if union else 0
        return 0.0

    def get_failure_patterns(self):
        failures = [ep for ep in self.episodes if ep.get("reward", 1) < 0]
        if not failures:
            return []
        action_counts = Counter(ep["action"] for ep in failures)
        return action_counts.most_common()
```

## 5. Planning Strategies

### 5.1 Chain-of-Thought (CoT)

```python
class ChainOfThought:
    def __init__(self, llm):
        self.llm = llm

    def solve(self, problem: str) -> str:
        prompt = f"Solve step by step:\nProblem: {problem}\n\nLet's think step by step:\nStep 1:"
        response = self.llm(prompt)
        return self.extract_answer(response)

    def solve_with_verification(self, problem: str) -> str:
        paths = []
        for _ in range(5):
            path = self.solve(problem)
            verification = self.verify(path)
            paths.append((path, verification))
        answers = {}
        for path, _ in paths:
            answer = self.extract_answer(path)
            answers[answer] = answers.get(answer, 0) + 1
        return max(answers, key=answers.get)

    def verify(self, reasoning: str) -> bool:
        verification_prompt = f"Is this reasoning correct? Check each step:\n{reasoning}\nIs there any error? Answer YES or NO:"
        response = self.llm(verification_prompt)
        return "YES" in response.upper()

    def extract_answer(self, response):
        if "Answer:" in response:
            return response.split("Answer:")[-1].strip()
        return response.strip()
```

#### Step-by-Step

1. **Problem Framing**: Present the problem explicitly with clear context and ask the LLM to "think step by step" to trigger decomposition behavior.
2. **Step Generation**: LLM generates numbered intermediate reasoning steps, breaking down the problem into smaller sub-problems with explicit intermediate conclusions.
3. **Sequential Logic**: Each step builds on previous steps, creating a chain of logical dependencies that forces the model to maintain internal consistency.
4. **Answer Extraction**: After all steps, extract the final answer from the LLM output (between "Answer:" marker or last logical conclusion).
5. **Verification Loop**: Re-prompt LLM to check each step independently for correctness, detecting logical errors or unsupported claims.
6. **Majority Voting**: Run multiple reasoning paths (5+ times) and return the most common answer, reducing impact of single reasoning errors.

#### Code Example

```python
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ReasoningStep:
    number: int
    content: str
    conclusion: str
    is_verified: bool = False

@dataclass
class CoTResult:
    problem: str
    reasoning_path: List[ReasoningStep]
    final_answer: str
    confidence: float
    verification_passed: bool

class ChainOfThought:
    """Chain-of-Thought reasoning with verification and voting."""
    
    def __init__(self, llm_callable, num_paths: int = 5):
        self.llm = llm_callable
        self.num_paths = num_paths
        self.results_history: List[CoTResult] = []

    def solve(self, problem: str) -> str:
        """Single reasoning path."""
        prompt = f"""Solve this problem step by step.

Problem: {problem}

Think step by step:
Step 1: """
        response = self.llm(prompt)
        return self._extract_answer(response)

    def solve_with_verification(self, problem: str) -> CoTResult:
        """Generate multiple paths, verify, and vote."""
        paths: List[CoTResult] = []
        
        for i in range(self.num_paths):
            # Step 1-4: Generate and extract one reasoning path
            reasoning = self._generate_reasoning(problem)
            steps = self._parse_steps(reasoning)
            answer = self._extract_answer(reasoning)
            
            # Step 5: Verify the reasoning
            verified = self._verify_reasoning(reasoning)
            
            path_result = CoTResult(
                problem=problem,
                reasoning_path=steps,
                final_answer=answer,
                confidence=0.9 if verified else 0.5,
                verification_passed=verified
            )
            paths.append(path_result)
        
        # Step 6: Majority vote on answer
        final_answer = self._majority_vote(paths)
        
        # Choose best reasoning path for return
        best_path = max(
            (p for p in paths if p.final_answer == final_answer),
            key=lambda p: p.confidence,
            default=paths[0]
        )
        
        self.results_history.append(best_path)
        return best_path

    def _generate_reasoning(self, problem: str) -> str:
        """Generate step-by-step reasoning."""
        prompt = f"""Solve this step by step.

Problem: {problem}

Work through this methodically:
Step 1:"""
        return self.llm(prompt)

    def _parse_steps(self, reasoning: str) -> List[ReasoningStep]:
        """Extract numbered steps from reasoning."""
        steps = []
        lines = reasoning.split("\n")
        current_step = None
        
        for line in lines:
            if line.strip().startswith("Step "):
                if current_step:
                    steps.append(current_step)
                # Parse "Step N: ..."
                try:
                    step_num = int(line.split(":")[0].split()[-1])
                    content = ":".join(line.split(":")[1:]).strip()
                    current_step = ReasoningStep(
                        number=step_num,
                        content=content,
                        conclusion=content
                    )
                except (ValueError, IndexError):
                    pass
        
        if current_step:
            steps.append(current_step)
        
        return steps

    def _extract_answer(self, reasoning: str) -> str:
        """Extract final answer from reasoning."""
        if "Answer:" in reasoning:
            return reasoning.split("Answer:")[-1].strip()
        elif "Final answer:" in reasoning.lower():
            idx = reasoning.lower().index("final answer:")
            return reasoning[idx + 12:].strip()
        else:
            # Last non-empty line is likely the answer
            lines = [l.strip() for l in reasoning.split("\n") if l.strip()]
            return lines[-1] if lines else ""

    def _verify_reasoning(self, reasoning: str) -> bool:
        """Verify correctness of reasoning."""
        verification_prompt = f"""Review this reasoning for errors.

Reasoning:
{reasoning}

Is this reasoning logically sound? Answer only YES or NO."""
        
        response = self.llm(verification_prompt)
        return "YES" in response.upper()

    def _majority_vote(self, paths: List[CoTResult]) -> str:
        """Select most common answer."""
        answers = {}
        for path in paths:
            answer = path.final_answer
            # Weight by confidence
            weight = path.confidence if path.verification_passed else path.confidence * 0.5
            answers[answer] = answers.get(answer, 0) + weight
        
        return max(answers, key=answers.get) if answers else ""

    def get_confidence_stats(self) -> Dict:
        """Return statistics on reasoning confidence."""
        if not self.results_history:
            return {}
        
        verified_count = sum(1 for r in self.results_history if r.verification_passed)
        avg_confidence = sum(r.confidence for r in self.results_history) / len(self.results_history)
        
        return {
            "total_problems": len(self.results_history),
            "verified_rate": verified_count / len(self.results_history),
            "avg_confidence": avg_confidence
        }

# Usage
def mock_llm(prompt: str) -> str:
    """Mock LLM for testing."""
    if "Step 1:" in prompt:
        return """Step 1: First, identify what we know. We have apples and oranges.
Step 2: Count the apples: 5 apples.
Step 3: Count the oranges: 3 oranges.
Step 4: Add them together: 5 + 3 = 8.
Answer: 8 total fruits."""
    return "YES"

cot = ChainOfThought(mock_llm, num_paths=3)
result = cot.solve_with_verification("If I have 5 apples and 3 oranges, how many fruits do I have?")
print(f"Answer: {result.final_answer}")
print(f"Verified: {result.verification_passed}")
print(f"Confidence: {result.confidence}")
```

#### Real-World Scenario

A financial analyst agent receives: "Company X spent $2M on R&D, $3M on marketing, $1M on ops. What's total spend and what % is R&D?" CoT generates: Step 1: List expenses (R&D=$2M, Marketing=$3M, Ops=$1M), Step 2: Sum = $2M+$3M+$1M = $6M, Step 3: R&D percentage = $2M/$6M = 33.3%. Verification checks: Are the numbers correct? Is the math correct? Yes to both. Majority voting (5 runs) all converge on $6M and 33.3%, confidence=0.95. Without CoT, the agent might jump to wrong answer; CoT forces step-by-step logic that's both more accurate and explainable to stakeholders.

#### Diagram

```mermaid
graph TD
    A["Problem"] --> B["Prompt: Think<br/>Step by Step"]
    B --> C["Step 1"]
    C --> D["Step 2"]
    D --> E["Step 3"]
    E --> F["Answer"]
    F --> G["Verify<br/>Each Step"]
    G --> H{"Valid?"}
    H -->|Yes| I["Add to Votes"]
    H -->|No| J["Low Weight"]
    I --> K["Repeat 5x"]
    J --> K
    K --> L["Majority Vote"]
    L --> M["Final Answer"]
```

### 5.2 Tree-of-Thoughts (ToT)

```python
class TreeOfThoughts:
    def __init__(self, llm, branching_factor=3, max_depth=5):
        self.llm = llm
        self.b = branching_factor
        self.max_depth = max_depth

    def solve(self, problem: str) -> str:
        root = {"thought": "", "state": problem, "value": 0}
        frontier = [root]
        for depth in range(self.max_depth):
            new_frontier = []
            for node in frontier:
                candidates = self.generate_candidates(node["state"], self.b)
                for candidate in candidates:
                    value = self.evaluate_state(candidate["state"])
                    new_frontier.append({"thought": candidate["thought"], "state": candidate["state"], "value": value, "parent": node})
            new_frontier.sort(key=lambda x: x["value"], reverse=True)
            frontier = new_frontier[:self.b]
            for node in frontier:
                if self.is_solution(node["state"]):
                    return self.reconstruct_path(node)
        best = max(frontier, key=lambda x: x["value"])
        return self.reconstruct_path(best)

    def generate_candidates(self, state, n):
        prompt = f"Current state: {state}\nGenerate {n} possible next steps. Format: Thought: <thought> | State: <new_state>"
        response = self.llm(prompt)
        return self.parse_candidates(response)

    def evaluate_state(self, state):
        prompt = f"Evaluate how promising this state is (0-1):\nState: {state}\nScore:"
        response = self.llm(prompt)
        try:
            return float(response.strip())
        except ValueError:
            return 0.5

    def is_solution(self, state):
        prompt = f"Is this a complete solution? Answer YES or NO.\nState: {state}"
        response = self.llm(prompt)
        return "YES" in response.upper()

    def reconstruct_path(self, node):
        path = []
        while node:
            path.append(node["thought"])
            node = node.get("parent")
        return "\n".join(reversed(path))
```

### 5.3 Reflexion Pattern

```python
class ReflexionAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.memories = []
        self.max_attempts = 3

    def run(self, task: str) -> Dict:
        for attempt in range(self.max_attempts):
            print(f"Attempt {attempt + 1}/{self.max_attempts}")
            result = self.execute_with_memory(task)
            if result["success"]:
                return result
            reflection = self.reflect(task, result)
            self.memories.append(reflection)
        return {"success": False, "error": "Max attempts reached"}

    def execute_with_memory(self, task: str) -> Dict:
        memories_context = self.get_relevant_memories(task)
        prompt = f"Task: {task}\n\nPrevious lessons learned:\n{memories_context}\n\nExecute the task step by step:"
        actions_taken = []
        state = prompt
        for step in range(10):
            response = self.llm(state)
            if "FINISHED" in response:
                return {"success": True, "actions": actions_taken, "output": response}
            action = self.parse_action(response)
            if action:
                result = self.execute_tool(action)
                actions_taken.append({"action": action, "result": result})
                state += f"\nObservation: {result}"
            else:
                state += f"\nThought: {response}"
        return {"success": False, "actions": actions_taken, "error": "Max steps"}

    def reflect(self, task: str, result: Dict) -> str:
        prompt = f"Task: {task}\nActions taken: {json.dumps(result.get('actions', []))}\nError: {result.get('error', 'Unknown')}\n\nWhat went wrong? What should be done differently next time?\nLesson learned:"
        return self.llm(prompt)

    def get_relevant_memories(self, task: str) -> str:
        if not self.memories:
            return "No previous attempts."
        task_words = set(task.lower().split())
        scored = []
        for mem in self.memories:
            mem_words = set(mem.lower().split())
            overlap = len(task_words & mem_words)
            scored.append((overlap, mem))
        scored.sort(reverse=True)
        top_memories = [mem for _, mem in scored[:3]]
        return "\n".join(top_memories)
```

## 6. Multi-Agent Systems

### 6.1 Agent Teams with Specialization

```python
class SpecializedAgent:
    def __init__(self, name: str, role: str, llm, tools: List[Tool]):
        self.name = name
        self.role = role
        self.llm = llm
        self.tools = tools
        self.memory = []

    def process(self, task: str, context: str = "") -> str:
        prompt = f"You are {self.name}, {self.role}.\nContext: {context}\nTask: {task}\nRespond with your expertise:"
        response = self.llm(prompt)
        self.memory.append({"task": task, "response": response})
        return response


class AgentTeam:
    def __init__(self, agents: List[SpecializedAgent], coordinator_llm):
        self.agents = {a.name: a for a in agents}
        self.coordinator = coordinator_llm

    def solve(self, task: str) -> Dict:
        subtasks = self.decompose(task)
        results = {}
        for subtask in subtasks:
            agent_name = subtask["agent"]
            if agent_name in self.agents:
                context = "\n".join(f"{k}: {v}" for k, v in results.items())
                result = self.agents[agent_name].process(subtask["description"], context)
                results[agent_name] = result
        final = self.synthesize(task, results)
        return {"subtask_results": results, "final": final}

    def decompose(self, task):
        prompt = f"Decompose this task into subtasks.\nAvailable agents: {', '.join(self.agents.keys())}\nTask: {task}\nRespond in JSON format:\n[{\"agent\": \"agent_name\", \"description\": \"subtask description\"}]"
        response = self.coordinator(prompt)
        return json.loads(response)

    def synthesize(self, task, results):
        context = "\n".join(f"{k}: {v}" for k, v in results.items())
        prompt = f"Task: {task}\nResults from agents:\n{context}\nSynthesize a final response:"
        return self.coordinator(prompt)
```

### 6.2 Agent Orchestration Patterns

```python
from enum import Enum

class OrchestrationPattern(Enum):
    SEQUENTIAL = "sequential"
    ROUND_ROBIN = "round_robin"
    DEBATE = "debate"
    HIERARCHICAL = "hierarchical"
    VOTING = "voting"

class Orchestrator:
    def __init__(self, agents, llm):
        self.agents = agents
        self.llm = llm

    def run(self, task: str, pattern: OrchestrationPattern):
        if pattern == OrchestrationPattern.SEQUENTIAL:
            return self.sequential(task)
        elif pattern == OrchestrationPattern.ROUND_ROBIN:
            return self.round_robin(task)
        elif pattern == OrchestrationPattern.DEBATE:
            return self.debate(task)
        elif pattern == OrchestrationPattern.HIERARCHICAL:
            return self.hierarchical(task)
        elif pattern == OrchestrationPattern.VOTING:
            return self.voting(task)

    def sequential(self, task):
        result = task
        for agent in self.agents:
            result = agent.process(f"Continue from: {result}")
        return result

    def round_robin(self, task, rounds=3):
        messages = [{"role": "user", "content": task}]
        for r in range(rounds):
            for agent in self.agents:
                response = self.llm(messages, agent=agent)
                messages.append({"role": "assistant", "content": response, "agent": agent.name})
        return messages

    def debate(self, task, rounds=3):
        positions = {agent.name: agent.process(task) for agent in self.agents}
        for r in range(rounds):
            for agent in self.agents:
                other_positions = {k: v for k, v in positions.items() if k != agent.name}
                context = f"Your position: {positions[agent.name]}\nOthers: {json.dumps(other_positions)}"
                positions[agent.name] = agent.process(context)
        return self.synthesize_debate(positions)

    def voting(self, task):
        votes = {agent.name: agent.process(task) for agent in self.agents}
        answer_counts = {}
        for _, answer in votes.items():
            answer_counts[answer] = answer_counts.get(answer, 0) + 1
        return max(answer_counts, key=answer_counts.get)
```

### 6.3 CrewAI-Style Agent Framework

```python
class CrewAIAgent:
    def __init__(self, role: str, goal: str, backstory: str, llm, tools=None):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.llm = llm
        self.tools = tools or []

    def execute_task(self, task: str, context: str = ""):
        prompt = f"Role: {self.role}\nGoal: {self.goal}\nBackstory: {self.backstory}\nContext: {context}\nTask: {task}\nExecute this task:"
        return self.llm(prompt)


class CrewTask:
    def __init__(self, description: str, agent: CrewAIAgent, expected_output: str = None):
        self.description = description
        self.agent = agent
        self.expected_output = expected_output
        self.context = []

    def execute(self):
        context_str = "\n".join(self.context)
        return self.agent.execute_task(self.description, context_str)


class Crew:
    def __init__(self, agents: List[CrewAIAgent], tasks: List[CrewTask], process: str = "sequential"):
        self.agents = {a.role: a for a in agents}
        self.tasks = tasks
        self.process = process

    def kickoff(self):
        results = {}
        if self.process == "sequential":
            for task in self.tasks:
                task.context = list(results.values())
                result = task.execute()
                results[task.agent.role] = result
        elif self.process == "hierarchical":
            manager = next(a for a in self.agents.values() if "manager" in a.role.lower())
            workers = [a for a in self.agents.values() if "manager" not in a.role.lower()]
            for task in self.tasks:
                assigned = manager.execute_task(f"Assign this task: {task.description}\nWorkers: {[w.role for w in workers]}")
                worker = next(w for w in workers if w.role in assigned)
                result = worker.execute_task(task.description)
                results[worker.role] = result
        return results
```

## 7. Agent Production Patterns

### 7.1 Guardrails

```python
class Guardrail:
    def check(self, input_text: str, output_text: str) -> bool:
        raise NotImplementedError

class ContentFilter(Guardrail):
    def __init__(self, forbidden_terms=None):
        self.forbidden_terms = forbidden_terms or ["violence", "hate speech", "explicit"]

    def check(self, input_text, output_text):
        for term in self.forbidden_terms:
            if term.lower() in output_text.lower():
                return False
        return True

class BudgetGuardrail(Guardrail):
    def __init__(self, max_cost_per_run: float):
        self.max_cost = max_cost_per_run
        self.total_cost = 0.0

    def check(self, input_text, output_text):
        estimated_cost = (len(input_text) + len(output_text)) * 0.00003
        if self.total_cost + estimated_cost > self.max_cost:
            return False
        self.total_cost += estimated_cost
        return True

class GuardrailManager:
    def __init__(self, guardrails: List[Guardrail]):
        self.guardrails = guardrails

    def validate(self, input_text: str, output_text: str) -> tuple[bool, str]:
        for guardrail in self.guardrails:
            if not guardrail.check(input_text, output_text):
                return False, f"Failed {type(guardrail).__name__}"
        return True, "Passed"
```

### 7.2 Human-in-the-Loop

```python
class HumanInTheLoop:
    def __init__(self, approval_threshold: float = 0.8):
        self.approval_threshold = approval_threshold

    def request_approval(self, action: Action, context: str) -> bool:
        print(f"\n=== HUMAN APPROVAL REQUIRED ===")
        print(f"Context: {context}")
        print(f"Action: {action.name}")
        print(f"Args: {action.args}")
        response = input("Approve? (y/n): ").lower()
        return response == 'y'

    def auto_approve(self, action: Action, confidence: float) -> bool:
        if confidence > self.approval_threshold:
            return True
        return self.request_approval(action, f"Low confidence ({confidence:.2f})")


class EscalationPolicy:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def handle_error(self, error: Exception, context: str, attempt: int) -> str:
        if attempt >= self.max_retries:
            return "ESCALATE_TO_HUMAN"
        if isinstance(error, ValueError):
            return "RETRY_WITH_DIFFERENT_INPUT"
        return "RETRY"
```

### 7.3 Observability

```python
import time
from dataclasses import dataclass, field

@dataclass
class AgentTrace:
    agent_id: str
    task: str
    start_time: float
    steps: List[Dict] = field(default_factory=list)
    total_cost: float = 0.0
    end_time: float = None
    status: str = "running"

    def record_step(self, step_type: str, input: str, output: str, duration: float, cost: float = 0.0):
        self.steps.append({
            "type": step_type, "input": input, "output": output,
            "duration": duration, "cost": cost, "timestamp": time.time()
        })
        self.total_cost += cost

    def finish(self, status: str = "completed"):
        self.end_time = time.time()
        self.status = status

    def to_dict(self):
        return {
            "agent_id": self.agent_id, "task": self.task,
            "duration": (self.end_time or time.time()) - self.start_time,
            "steps": len(self.steps), "total_cost": self.total_cost,
            "status": self.status
        }


class AgentLogger:
    def __init__(self):
        self.traces = {}

    def start_trace(self, agent_id: str, task: str) -> str:
        trace_id = f"{agent_id}_{time.time()}"
        self.traces[trace_id] = AgentTrace(agent_id=agent_id, task=task, start_time=time.time())
        return trace_id

    def end_trace(self, trace_id: str, status: str = "completed"):
        if trace_id in self.traces:
            self.traces[trace_id].finish(status)

    def get_metrics(self, agent_id: str = None) -> Dict:
        traces = [t for t in self.traces.values() if not agent_id or t.agent_id == agent_id]
        if not traces:
            return {}
        durations = [t.end_time - t.start_time for t in traces if t.end_time]
        costs = [t.total_cost for t in traces]
        return {
            "total_runs": len(traces),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "total_cost": sum(costs),
            "avg_cost": sum(costs) / len(costs) if costs else 0,
            "success_rate": sum(1 for t in traces if t.status == "completed") / len(traces)
        }
```

### 7.4 Error Recovery

```python
class RetryWithBackoff:
    def __init__(self, max_retries=3, base_delay=1.0, max_delay=60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def execute(self, fn, *args, **kwargs):
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    time.sleep(delay)
        raise last_exception


class FallbackChain:
    def __init__(self, strategies: List[Callable]):
        self.strategies = strategies

    def execute(self, *args, **kwargs):
        errors = []
        for strategy in self.strategies:
            try:
                return strategy(*args, **kwargs)
            except Exception as e:
                errors.append(e)
        raise Exception(f"All strategies failed: {errors}")
```

## 8. MCP (Model Context Protocol)

### 8.1 Overview

MCP is an open protocol (Anthropic) that standardizes how AI agents connect to external tools and data sources. It provides a unified interface for tool discovery, authentication, and execution.

```mermaid
graph TB
    subgraph "Agent / Host"
        A["LLM Application"]
        B["MCP Client"]
    end
    subgraph "MCP Protocol"
        C["MCP Transport<br/>(stdio/SSE)"]
        D["Capability<br/>Negotiation"]
    end
    subgraph "MCP Server"
        E["Tool Registry"]
        F["Resource<br/>Manager"]
        G["Prompt<br/>Templates"]
    end
    subgraph "External Systems"
        H["Databases"]
        I["APIs"]
        J["File Systems"]
        K["Vector Stores"]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    D --> F
    D --> G
    E --> H
    E --> I
    F --> J
    G --> K
```

### 8.2 MCP Server Implementation

```python
# MCP Server (Model Context Protocol)
class MCPServer:
    """MCP server that exposes tools and resources to AI agents."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: dict[str, MCPTool] = {}
        self.resources: dict[str, MCPResource] = {}
        self.prompts: dict[str, MCPPrompt] = {}

    def register_tool(self, name: str, description: str,
                       input_schema: dict, handler: callable):
        self.tools[name] = MCPTool(name, description, input_schema, handler)

    def register_resource(self, uri: str, name: str,
                           mime_type: str, handler: callable):
        self.resources[uri] = MCPResource(uri, name, mime_type, handler)

    def register_prompt(self, name: str, description: str,
                         template: str, arguments: list[dict]):
        self.prompts[name] = MCPPrompt(name, description, template, arguments)

    def handle_request(self, request: dict) -> dict:
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return {"tools": [t.to_dict() for t in self.tools.values()]}
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            tool = self.tools.get(tool_name)
            if not tool:
                return {"error": f"Tool '{tool_name}' not found"}
            try:
                result = tool.handler(**arguments)
                return {"content": [{"type": "text", "text": str(result)}]}
            except Exception as e:
                return {"error": str(e)}
        elif method == "resources/list":
            return {"resources": [r.to_dict() for r in self.resources.values()]}
        elif method == "resources/read":
            uri = params.get("uri")
            resource = self.resources.get(uri)
            if not resource:
                return {"error": f"Resource '{uri}' not found"}
            content = resource.handler()
            return {"contents": [{"uri": uri, "mimeType": resource.mime_type,
                                   "text": content}]}
        elif method == "prompts/list":
            return {"prompts": [p.to_dict() for p in self.prompts.values()]}
        else:
            return {"error": f"Unknown method: {method}"}

    def serve_stdio(self):
        """Run MCP server over stdin/stdout."""
        import sys, json
        for line in sys.stdin:
            request = json.loads(line.strip())
            response = self.handle_request(request)
            print(json.dumps(response), flush=True)

    def serve_sse(self, host: str = "localhost", port: int = 8000):
        """Run MCP server over SSE (Server-Sent Events)."""
        from http.server import HTTPServer, BaseHTTPRequestHandler

        class MCPHandler(BaseHTTPRequestHandler):
            server_instance = self

            def do_POST(self):
                content_length = int(self.headers["Content-Length"])
                body = self.rfile.read(content_length)
                request = json.loads(body)
                response = self.server_instance.handle_request(request)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

        server = HTTPServer((host, port), MCPHandler)
        print(f"MCP server listening on {host}:{port}")
        server.serve_forever()


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: dict
    handler: callable

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


@dataclass
class MCPResource:
    uri: str
    name: str
    mime_type: str
    handler: callable

    def to_dict(self):
        return {"uri": self.uri, "name": self.name, "mimeType": self.mime_type}


@dataclass
class MCPPrompt:
    name: str
    description: str
    template: str
    arguments: list[dict]

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments
        }


# MCP Client (connects to MCP servers)
class MCPClient:
    def __init__(self):
        self.servers: dict[str, MCPServer] = {}
        self.tool_cache: dict = {}

    def connect_stdio(self, name: str, server: MCPServer):
        self.servers[name] = server

    def list_tools(self) -> list[dict]:
        all_tools = []
        for name, server in self.servers.items():
            response = server.handle_request({"method": "tools/list"})
            for tool in response.get("tools", []):
                tool["server"] = name
                all_tools.append(tool)
        return all_tools

    def call_tool(self, server_name: str, tool_name: str,
                   arguments: dict) -> str:
        server = self.servers.get(server_name)
        if not server:
            return f"Error: Server '{server_name}' not found"
        response = server.handle_request({
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        })
        return response.get("content", [{}])[0].get("text", str(response))


# Example: Database MCP server
class DatabaseMCPServer(MCPServer):
    def __init__(self):
        super().__init__("database-server")
        self.register_tool(
            "query", "Execute SQL query",
            {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL query"}
                },
                "required": ["sql"]
            },
            self.execute_query
        )
        self.register_resource(
            "db://schemas", "Database Schemas", "application/json",
            lambda: json.dumps({"tables": ["users", "orders", "products"]})
        )

    def execute_query(self, sql: str) -> str:
        return f"Query results for: {sql[:50]}..."
```

## 9. Agent Evaluation and Observability

### 9.1 Evaluation Framework

```python
class AgentEvaluator:
    def __init__(self, llm_as_judge=None):
        self.judge = llm_as_judge
        self.results = []

    def evaluate_task(self, task: str, agent_output: str,
                       expected_output: str = None) -> dict:
        metrics = {
            "task": task,
            "output_length": len(agent_output),
            "contains_error_indicators": self._check_errors(agent_output),
            "tool_calls": self._count_tool_calls(agent_output),
        }

        if expected_output:
            metrics["exact_match"] = agent_output.strip() == expected_output.strip()
            metrics["rouge_l"] = self._rouge_l(agent_output, expected_output)
            metrics["semantic_similarity"] = self._semantic_similarity(
                agent_output, expected_output
            )

        if self.judge:
            metrics["judge_score"] = self._judge_evaluation(
                task, agent_output
            )

        self.results.append(metrics)
        return metrics

    def _check_errors(self, text: str) -> bool:
        error_indicators = ["error:", "exception", "failed", "unable to",
                           "could not", "timeout", "not found"]
        return any(indicator in text.lower() for indicator in error_indicators)

    def _count_tool_calls(self, text: str) -> int:
        return text.count("Action:") + text.count("tool_call")

    def _rouge_l(self, candidate: str, reference: str) -> float:
        cand_words = candidate.lower().split()
        ref_words = reference.lower().split()
        lcs = self._longest_common_subsequence(cand_words, ref_words)
        precision = lcs / len(cand_words) if cand_words else 0
        recall = lcs / len(ref_words) if ref_words else 0
        if precision + recall == 0:
            return 0
        return 2 * precision * recall / (precision + recall)

    def _longest_common_subsequence(self, a: list, b: list) -> int:
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if a[i - 1] == b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        return dp[m][n]

    def _semantic_similarity(self, text1: str, text2: str) -> float:
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union) if union else 0

    def _judge_evaluation(self, task: str, output: str) -> float:
        prompt = f"""Evaluate this agent's response for:
1. Correctness (1-5)
2. Completeness (1-5)
3. Clarity (1-5)

Task: {task}
Response: {output}

Score (average):"""

        score_text = self.judge(prompt) if self.judge else "4"
        try:
            return float(score_text.strip())
        except (ValueError, TypeError):
            return 3.0

    def aggregate_metrics(self) -> dict:
        if not self.results:
            return {}
        return {
            "total_evaluations": len(self.results),
            "avg_output_length": np.mean([r["output_length"] for r in self.results]),
            "error_rate": sum(1 for r in self.results if r["contains_error_indicators"]) / len(self.results),
            "avg_tool_calls": np.mean([r["tool_calls"] for r in self.results]),
            "avg_judge_score": np.mean([r.get("judge_score", 0) for r in self.results if "judge_score" in r])
        }


class AgentObservability:
    def __init__(self):
        self.traces: dict = {}
        self.metrics: dict = defaultdict(list)

    def start_trace(self, agent_id: str, task: str) -> str:
        trace_id = f"{agent_id}_{int(time.time())}"
        self.traces[trace_id] = {
            "agent_id": agent_id,
            "task": task,
            "start_time": time.time(),
            "steps": [],
            "status": "running",
            "total_cost": 0.0
        }
        return trace_id

    def record_step(self, trace_id: str, step_type: str,
                     input_text: str, output_text: str, duration: float,
                     token_usage: int = 0, cost: float = 0.0):
        trace = self.traces.get(trace_id)
        if trace:
            trace["steps"].append({
                "type": step_type,
                "input_length": len(input_text),
                "output_length": len(output_text),
                "duration_s": duration,
                "tokens": token_usage,
                "cost": cost,
                "timestamp": time.time()
            })
            trace["total_cost"] += cost

    def end_trace(self, trace_id: str, status: str = "completed"):
        trace = self.traces.get(trace_id)
        if trace:
            trace["end_time"] = time.time()
            trace["status"] = status
            trace["total_duration"] = trace["end_time"] - trace["start_time"]

            # Record aggregate metrics
            self.metrics["total_duration"].append(trace["total_duration"])
            self.metrics["total_cost"].append(trace["total_cost"])
            self.metrics["step_count"].append(len(trace["steps"]))
            self.metrics["status"].append(status)

    def get_agent_dashboard(self, agent_id: str = None) -> dict:
        traces = [t for t in self.traces.values()
                  if not agent_id or t["agent_id"] == agent_id]
        if not traces:
            return {}

        durations = [t["total_duration"] for t in traces if "total_duration" in t]
        costs = [t["total_cost"] for t in traces]
        step_counts = [len(t["steps"]) for t in traces]
        completed = sum(1 for t in traces if t["status"] == "completed")

        return {
            "total_runs": len(traces),
            "avg_duration_s": np.mean(durations) if durations else 0,
            "p95_duration_s": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else 0,
            "total_cost": sum(costs),
            "avg_cost_per_run": np.mean(costs) if costs else 0,
            "avg_steps_per_run": np.mean(step_counts) if step_counts else 0,
            "success_rate": completed / len(traces) * 100 if traces else 0,
            "tokens_used": sum(
                sum(s["tokens"] for s in t["steps"])
                for t in traces if "steps" in t
            )
        }

    def get_llm_usage_report(self) -> dict:
        total_tokens = sum(
            sum(s["tokens"] for s in t["steps"] if "tokens" in s)
            for t in self.traces.values()
        )
        total_cost = sum(t["total_cost"] for t in self.traces.values())
        return {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "cost_per_run": total_cost / len(self.traces) if self.traces else 0
        }
```

### 9.2 Production Failure Modes

```python
class AgentFailureDetector:
    """Detects and classifies agent failures in production."""

    FAILURE_TYPES = {
        "hallucination": {
            "description": "Agent fabricates tool results or facts",
            "severity": "critical",
            "detection": [
                "Confidence score < threshold",
                "Contradicts known facts",
                "Refers to non-existent tool outputs"
            ],
            "mitigation": [
                "Add result verification step",
                "Implement fact-checking against knowledge base",
                "Require citations from tool outputs",
                "Use temperature < 0.3 for factual tasks"
            ]
        },
        "tool_misuse": {
            "description": "Agent selects wrong tool for the task",
            "severity": "high",
            "detection": [
                "Tool call returns error or unexpected result",
                "Same tool called multiple times with same args",
                "Tool input doesn't match task requirements"
            ],
            "mitigation": [
                "Improve tool descriptions",
                "Add input validation before tool execution",
                "Implement tool selection validation",
                "Reduce tool count per agent"
            ]
        },
        "infinite_loop": {
            "description": "Agent repeats same action without progress",
            "severity": "high",
            "detection": [
                "Action history contains repeated patterns",
                "No progress toward task completion",
                "Tool call count exceeds threshold"
            ],
            "mitigation": [
                "Set max iterations (hard limit)",
                "Track action diversity score",
                "Implement loop detection (duplicate action > N times)",
                "Add forced progression: require different action each turn"
            ]
        },
        "context_window_overflow": {
            "description": "Agent exceeds LLM context window",
            "severity": "medium",
            "detection": [
                "Token count approaching limit",
                "Error from LLM API (context length exceeded)",
                "Early truncation of conversation history"
            ],
            "mitigation": [
                "Implement sliding window memory",
                "Summarize older context",
                "Use models with larger context (128K+ tokens)",
                "Compress tool outputs before adding to context"
            ]
        },
        "cost_explosion": {
            "description": "Agent exceeds budget due to excessive LLM calls",
            "severity": "high",
            "detection": [
                "Cost per run exceeds threshold",
                "Excessive token usage",
                "Too many retry attempts"
            ],
            "mitigation": [
                "Set per-run token budget",
                "Implement cost tracking guardrail",
                "Use smaller models for simple tasks",
                "Cache common LLM responses"
            ]
        }
    }

    def detect_failure(self, trace: dict) -> list[dict]:
        failures = []

        # Check for infinite loops
        if self._detect_loop(trace):
            failures.append({
                "type": "infinite_loop",
                "details": self.FAILURE_TYPES["infinite_loop"]
            })

        # Check for tool misuse
        if self._detect_tool_misuse(trace):
            failures.append({
                "type": "tool_misuse",
                "details": self.FAILURE_TYPES["tool_misuse"]
            })

        # Check for cost explosion
        if trace.get("total_cost", 0) > 1.0:  # $1 threshold
            failures.append({
                "type": "cost_explosion",
                "details": self.FAILURE_TYPES["cost_explosion"]
            })

        return failures

    def _detect_loop(self, trace: dict) -> bool:
        steps = trace.get("steps", [])
        if len(steps) < 10:
            return False
        recent_actions = [s.get("type") for s in steps[-10:] if s.get("type")]
        from collections import Counter
        counts = Counter(recent_actions)
        most_common = counts.most_common(1)
        return most_common and most_common[0][1] > 5

    def _detect_tool_misuse(self, trace: dict) -> bool:
        steps = trace.get("steps", [])
        error_steps = [s for s in steps if "error" in s.get("output", "").lower()]
        return len(error_steps) > len(steps) * 0.3

    def classify_severity(self, trace: dict) -> str:
        failures = self.detect_failure(trace)
        if any(f["details"]["severity"] == "critical" for f in failures):
            return "critical"
        elif any(f["details"]["severity"] == "high" for f in failures):
            return "high"
        elif failures:
            return "medium"
        return "low"


class AgentGuardrailManager:
    def __init__(self):
        self.guardrails = []

    def add_guardrail(self, name: str, check_fn: callable,
                       action: str = "block"):
        self.guardrails.append({
            "name": name,
            "check": check_fn,
            "action": action
        })

    def check_all(self, input_text: str, output_text: str,
                   trace: dict = None) -> list[dict]:
        results = []
        for guardrail in self.guardrails:
            try:
                passed = guardrail["check"](input_text, output_text, trace)
                if not passed:
                    results.append({
                        "guardrail": guardrail["name"],
                        "action": guardrail["action"],
                        "passed": False
                    })
            except Exception as e:
                results.append({
                    "guardrail": guardrail["name"],
                    "action": guardrail["action"],
                    "passed": False,
                    "error": str(e)
                })
        return results


# Production-ready agent with guardrails and monitoring
class ProductionAgent:
    def __init__(self, llm, tools: list, max_steps: int = 20,
                 max_cost: float = 0.50):
        self.agent = ReActAgent(llm, tools)
        self.monitor = AgentObservability()
        self.guardrails = AgentGuardrailManager()
        self.failure_detector = AgentFailureDetector()
        self.max_steps = max_steps
        self.max_cost = max_cost

        # Default guardrails
        self.guardrails.add_guardrail(
            "budget", lambda i, o, t: (t or {}).get("total_cost", 0) < max_cost
        )
        self.guardrails.add_guardrail(
            "max_steps", lambda i, o, t: len((t or {}).get("steps", [])) < max_steps
        )
        self.guardrails.add_guardrail(
            "toxic_output", lambda i, o, t: not self._is_toxic(o)
        )

    def run(self, task: str) -> dict:
        trace_id = self.monitor.start_trace("production_agent", task)

        try:
            result = self.agent.run(task)
            self.monitor.end_trace(trace_id, "completed")

            # Check for failures
            trace = self.monitor.traces[trace_id]
            failures = self.failure_detector.detect_failure(trace)
            guardrails = self.guardrails.check_all(task, str(result), trace)

            return {
                "result": result,
                "trace_id": trace_id,
                "failures": failures,
                "guardrails": guardrails,
                "dashboard": self.monitor.get_agent_dashboard()
            }

        except Exception as e:
            self.monitor.end_trace(trace_id, "failed")
            return {
                "error": str(e),
                "trace_id": trace_id,
                "failures": [{"type": "runtime_error", "message": str(e)}]
            }

    def _is_toxic(self, text: str) -> bool:
        toxic_patterns = ["hate", "violence", "abuse"]
        return any(p in str(text).lower() for p in toxic_patterns)
```

## 10. Agent Framework Comparison

### 10.1 Detailed Comparison

| Framework | Architecture | State Management | Tool Calling | Best For |
|-----------|-------------|-----------------|--------------|----------|
| LangChain | Agent + Tool + Chain | External memory | Function calling + custom | Quick prototyping, PoCs |
| LangGraph | State graph (nodes + edges) | Built-in graph state | Tool nodes in graph | Complex state machines, workflows |
| AutoGen | Conversable agents | Agent conversation history | Function calling | Multi-agent conversations |
| CrewAI | Crew + Process + Agent | Sequential/hierarchical | Role-based tool access | Task delegation, structured teams |
| Semantic Kernel | Plugin-based pipeline | Semantic memory | Plugin connectors | Enterprise .NET, Microsoft ecosystem |
| BabyAGI | Task queue + agent loop | Vector store | External tools | Autonomous task management |
| MCP-based | Client-Server protocol | Per-server state | MCP tools via protocol | Standardized tool access |

### 10.2 Selection Guide

```python
class AgentFrameworkSelector:
    def __init__(self):
        self.frameworks = {
            "langchain": {
                "strength": "rapid_prototyping",
                "complexity": "low",
                "use_case": "Simple RAG, single-tool agents",
                "scalability": "medium",
                "evaluation": "Manual testing"
            },
            "langgraph": {
                "strength": "complex_workflows",
                "complexity": "high",
                "use_case": "Multi-step reasoning, human-in-loop",
                "scalability": "high",
                "evaluation": "Graph-based testing"
            },
            "crewai": {
                "strength": "role_based_teams",
                "complexity": "medium",
                "use_case": "Content generation, research teams",
                "scalability": "medium",
                "evaluation": "Task completion metrics"
            },
            "autogen": {
                "strength": "conversational_agents",
                "complexity": "medium",
                "use_case": "Coding agents, debate systems",
                "scalability": "medium",
                "evaluation": "Conversation metrics"
            }
        }

    def recommend(self, requirements: dict) -> str:
        if requirements.get("state_machine"):
            return "langgraph"
        elif requirements.get("role_based"):
            return "crewai"
        elif requirements.get("conversation"):
            return "autogen"
        elif requirements.get("rapid_prototype"):
            return "langchain"

        # Scoring based on requirements
        scores = {}
        for name, info in self.frameworks.items():
            score = 0
            for req, weight in requirements.get("weights", {}).items():
                if req in info.get("tags", []):
                    score += weight
            scores[name] = score

        return max(scores, key=scores.get) if scores else "langchain"

    def deployment_considerations(self, framework: str) -> dict:
        considerations = {
            "langchain": {
                "deployment": "Standard API server",
                "monitoring": "LangSmith, LangFuse",
                "scaling": "Horizontal with request queue",
                "failure_modes": "Context overflow, tool timeout"
            },
            "langgraph": {
                "deployment": "Stateful service + checkpoint store",
                "monitoring": "LangSmith tracing, custom metrics",
                "scaling": "Checkpoint persistence + horizontal pods",
                "failure_modes": "Graph deadlock, state corruption"
            },
            "crewai": {
                "deployment": "Crew as API endpoint",
                "monitoring": "Step-by-step logging",
                "scaling": "Parallel crews, task queues",
                "failure_modes": "Agent miscommunication, cascade failures"
            }
        }
        return considerations.get(framework, {})
```

## 11. Exercise Problems

**Problem 1**: Implement a ReAct agent with tools for web search, calculator, and database query. Design the prompt format and tool calling mechanism.

**Problem 2**: Build a multi-agent system with a coordinator agent that delegates tasks to specialized sub-agents (researcher, writer, reviewer) and synthesizes results.

**Problem 3**: Implement a Reflexion agent that learns from its mistakes. Test on a multi-step reasoning task and measure improvement over attempts.

**Problem 4**: Design a production guardrail system with content filtering, budget limits, and rate limiting. Implement a retry mechanism with exponential backoff.

**Problem 5**: Build an observability system that traces agent reasoning, tracks costs, and measures success rates. Generate a dashboard-ready report.

---

## Related

- [Databases](../../08-databases/) — Vector search, embeddings storage
- [Python Backend](../../03-backend/) — ML inference APIs
- [Cloud Platforms](../../05-cloud/) — GPU/TPU infrastructure
- [Data Engineering](../../02-data-engineering/) — Training data pipelines
- [Performance Engineering](../../18-performance-engineering/) — Model optimization


## Real-World Agent Example: Customer Support Bot

```javascript
// Complete agent implementation for support tickets
class SupportAgent {
  constructor(llm) {
    this.llm = llm;
    this.tools = {
      createTicket: (issue) => ({ id: 'TKT-123', status: 'open' }),
      searchKnowledge: (query) => ([{ article: 'FAQ-1', relevance: 0.95 }]),
      escalateToHuman: (reason) => ({ assigned: 'support@company.com' })
    };
  }

  async handleRequest(userMessage) {
    // 1. Perception: Parse user request
    const perception = { input: userMessage, confidence: 0.92 };
    
    // 2. Reasoning: LLM decides action
    const decision = await this.llm.decide({
      userMessage,
      availableTools: Object.keys(this.tools),
      context: 'customer support'
    });
    
    // 3. Action: Execute chosen tool
    const result = this.tools[decision.tool]?.(decision.args);
    
    // 4. Observe: Process result
    return { response: decision.message, action: result };
  }
}
```

### Common Agent Failure Cases

| Case | Problem | Solution |
|------|---------|----------|
| Hallucination | Agent fabricates tool results | Add result verification |
| Tool misuse | Wrong tool selected | Add tool descriptions |
| Infinite loops | Agent repeats same action | Track action history |
| Context loss | Forgets previous steps | Maintain session memory |

