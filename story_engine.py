# story_engine.py
import os
import json
import re
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
# NOTE: memory_store.py must contain the JsonMessageHistoryStore class
from memory_store import JsonMessageHistoryStore 

# ============================================================
# ENV + LANGSMITH
# ============================================================
load_dotenv()

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GEMINI_API_KEY not set in .env")

LANGSMITH_ENABLED = os.getenv("LANGSMITH_TRACING", "").lower() == "true"

# ============================================================
# MEMORY
# ============================================================
MEMORY_PATH = os.getenv("MEMORY_DB_PATH", "sessions.json")
_store = JsonMessageHistoryStore(MEMORY_PATH)

# --- Helper Functions for Message Conversion ---
def _msg_to_dict(m: BaseMessage) -> Dict[str, str]:
    """Converts a LangChain message object to a simple dictionary for storage."""
    role = "human" if isinstance(m, HumanMessage) else "ai"
    return {"role": role, "content": m.content}

def _dict_to_msg(m: Dict[str, str]) -> BaseMessage:
    """Converts a simple dictionary from storage back to a LangChain message object."""
    return HumanMessage(content=m["content"]) if m["role"] == "human" \
        else AIMessage(content=m["content"])

def _get_history(session_id: str) -> List[BaseMessage]:
    """Retrieves the history for a session."""
    return [_dict_to_msg(m) for m in _store.get_history(session_id)]

def _save_history(session_id: str, messages: List[BaseMessage]):
    """Saves the history for a session."""
    _store.set_history(session_id, [_msg_to_dict(m) for m in messages])

def get_last_story(session_id: str) -> Optional[str]:
    """Retrieves the most recently saved final story text."""
    for msg in reversed(_get_history(session_id)):
        if isinstance(msg, AIMessage) and msg.content.startswith("[FINAL STORY]"):
            return msg.content.replace("[FINAL STORY]", "").strip()
    return None

def _has_story(session_id: str) -> bool:
    """Checks if a final story exists in the session history."""
    return get_last_story(session_id) is not None

# ============================================================
# LLMs — Gemini Flash 2.5 (FAST)
# ============================================================
def _llm(temp: float = 0.6) -> ChatGoogleGenerativeAI:
    """Factory function for creating ChatGoogleGenerativeAI instances."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=temp
    )

_story_llm = _llm(0.65)   # Creative (for story writing/rewriting)
_judge_llm = _llm(0.0)    # Strict (for safety/JSON/Intent Classification)
_chat_llm  = _llm(0.4)    # Balanced (for short chat replies)

def _invoke(llm: ChatGoogleGenerativeAI, prompt: str, run_name: str = "run") -> str:
    """Invokes the LLM with optional LangSmith tracing."""
    cfg = {"run_name": run_name} if LANGSMITH_ENABLED else {}
    res = llm.invoke(prompt, config=cfg)
    return res.content

# ============================================================
# JSON SAFETY (J2)
# ============================================================
def _safe_json(raw: str) -> Dict[str, Any]:
    """Safely parses JSON output from an LLM, providing defaults on failure."""
    # Note: Added 'instruction' key for Intent Classifier parsing, and 'unsafe'/'hint' for Judge parsing.
    defaults = {"unsafe": False, "hint": "", "intent": "chat", "instruction": raw}
    if not isinstance(raw, str):
        return defaults
    
    # Use regex to find the potential JSON object
    txt = raw.strip().strip("`").strip()
    m = re.search(r"\{.*\}", txt, flags=re.DOTALL)
    if m:
        txt = m.group(0)
    
    try:
        obj = json.loads(txt)
    except:
        return defaults
    
    # Return only the keys relevant for all LLM JSON outputs
    # This generalizes the function to handle both judge and intent JSON outputs
    result = {}
    for key, default_value in defaults.items():
        # Check if the key exists in the parsed object, otherwise use the default
        result[key] = obj.get(key, default_value)
        # Ensure boolean keys like 'unsafe' are correctly cast if the LLM output a string
        if isinstance(default_value, bool) and isinstance(result[key], str):
             result[key] = result[key].lower() == 'true'

    return result

# ============================================================
# LLM PROMPT TOOLS (The Tool Definitions)
# ============================================================

# Tool 1: Intent Classifier (Replaces hardcoded HINTS)
INTENT_CLASSIFIER_PROMPT = lambda txt, has_story: f"""
You are a routing system for a story generator. Your task is to classify the user's request 
and extract the necessary instruction. Only use the available intents.

Current Session Status: {'A story is active.' if has_story else 'No story is active.'}
Mention Various themes in prompts for all the tools and Dont use hardcoded one use routing .The prompts should very much clear take various possibilites

Possible intents:
- 'new_story': The user wants a new story. **Example:** "Tell me a story about a brave knight."
- 'refine': The user wants to modify, extend, or improve the active story. Only use this if a story is active. **Example:** "Make the king a little friendlier."
- 'chat': The user is making a general comment, asking a question, or giving a simple reply. **Example:** "That was a good story, thanks."

Return JSON ONLY.

{{
  "intent": "<'new_story' | 'refine' | 'chat'>",
  "instruction": "<The core request text (e.g., the theme or the change). Extract character names or specific themes if mentioned, and keep it concise.>"
}}

User Request: "{txt}"
"""

# Tool 2: Story Generator (Uses _story_llm) - UPDATED FOR STRICTER REFUSAL OF UNSAFE THEMES
STORY_PROMPT = lambda req: f"""
Write a short bedtime story (180–300 words) for kids age 5–10.
The story must be Warm, positive, and use simple sentences. 
STRICT RULE: Prohibit ANY content related to violence, fear, danger, sadness, death, or loss. 
If the requested Theme/Topic: "{req}" contains an element that cannot be made 100% positive (e.g., 'murder,' 'fight,' 'tragedy'), **you must ignore that unsafe element entirely** and write a simple, safe story about a happy, unrelated subject (e.g., sharing a toy or finding a flower).
Theme/Topic: "{req}"
End with a gentle moral.
"""

# Tool 3: Story Evaluator (Uses _judge_llm) - UPDATED FOR EXPLICIT TOOL STRUCTURE AND STRICTER SAFETY
JUDGE_PROMPT = lambda s: f"""
You are the **Story Evaluation Tool**. Your purpose is to strictly judge the provided story against child safety rules (age 5-10) and offer constructive feedback.

Safety Rules (STRICT REFUSAL IF VIOLATED): 
- NO explicit acts of violence (e.g., fighting, striking, murder).
- NO concepts of death, injury, loss, or grief (even if implied, like "tragic loss" or "taken unjustly").
- NO intense negative emotions (fear, terror, profound sadness) that are not immediately and fully resolved.
- Story must be 100% positive, warm, and gentle throughout.

Quality Rules: Story must be 180-300 words, end with a moral.

Output is MANDATORY JSON format with two parameters:
1. "unsafe" (Boolean): true if the story violates ANY safety rule above, false otherwise.
2. "hint" (String): A short, single-sentence improvement suggestion for the writer (e.g., 'Make it a little shorter' or 'Add a blue flower'), OR an empty string "" if the story is perfect or unsafe.

Return JSON ONLY:
{{
  "unsafe": false,
  "hint": "<Improvement hint or empty string>"
}}

Story to Evaluate: \"\"\"{s}\"\"\"
"""

# Tool 4: Revision Evaluator (Uses _story_llm, acting as a rewrite tool)
IMPROVE_PROMPT = lambda story, hint: f"""
Rewrite the ENTIRE story, applying this hint: "{hint}".
Keep it safe, gentle, 180–300 words, with a clear moral at the end.
Return ONLY the improved story text. Do not add any commentary or prefix.
Story to revise: \"\"\"{story}\"\"\"
"""

# Tool 5: Chat Responder (Uses _chat_llm)
CHAT_PROMPT = lambda ctx, user: f"""
You are a friendly story assistant. Reply in 1–2 friendly sentences. 
Do NOT start a a story or ask for a story request unless the user clearly asks for one.
Story so far (for context): \"\"\"{ctx}\"\"\"
User: "{user}"
"""

REFUSAL = "I can't write that safely for kids, as the theme might involve danger or fear, or an event of significant loss. However, I can offer a gentle, positive version if you want to try a similar topic."

# ============================================================
# INTENT & CONTEXT EXTRACTION (TOOL-BASED ROUTING)
# ============================================================

def extract_context_and_detect_intent_tool_based(txt: str, has_story: bool) -> Tuple[str, str]:
    """
    Detects intent and extracts the core instruction using the LLM Intent Classification Tool (Tool 1).
    Returns (intent, request/instruction).
    """
    
    # 1. Invoke the LLM Intent Classification Tool
    raw_json = _invoke(
        _judge_llm, # Use the strict LLM for reliable JSON output
        INTENT_CLASSIFIER_PROMPT(txt, has_story),
        "intent_classifier_tool"
    )
    
    # 2. Safely Parse the Output
    parsed_data = _safe_json(raw_json) 
    intent = parsed_data.get("intent", "chat").lower()
    instruction = parsed_data.get("instruction", txt).strip()
    
    # 3. Post-Classification Logic (Safety Check)
    if intent == "refine" and not has_story:
        intent = "new_story" 
        
    return intent, instruction

# ============================================================
# STORY PIPELINE FUNCTIONS (LLM Tool Implementations)
# ============================================================

def generate_with_judge_loop(session_id: str, req: str) -> Tuple[str, List[str]]:
    """
    Implements the story generation, evaluation (Tool 3), and optional revision (Tool 4) loop.
    Returns (final_story_text, suggestions_applied).
    """
    
    # 1) First Draft (Tool 2: Story Generator)
    draft = _invoke(_story_llm, STORY_PROMPT(req), "story_draft")

    # 2) Judge Safety (Tool 3: Story Evaluator)
    judge = _safe_json(_invoke(_judge_llm, JUDGE_PROMPT(draft), "judge"))
    
    if judge.get("unsafe"):
        return REFUSAL, []

    # 3) Improve if needed (Tool 4: Revision Evaluator)
    final_story = draft
    suggestions = []
    
    if judge.get("hint"):
        final_story = _invoke(_story_llm, IMPROVE_PROMPT(draft, judge["hint"]), "rewrite")
        suggestions.append(judge["hint"])

    # 4) Save final story
    history = _get_history(session_id)
    history.append(AIMessage(content=f"[FINAL STORY]\n{final_story}"))
    _save_history(session_id, history)
    
    return final_story, suggestions

def refine_with_human_feedback(session_id: str, instruction: str) -> str:
    """
    Refines the last story based on direct user instruction (Tool 4: Revision Evaluator).
    CRITICAL: The refined story is run through the Judge (Tool 3) for safety.
    """
    last = get_last_story(session_id)
    if not last:
        return "I don't have a story right now. Could you ask me to tell you a new one?"

    # 1. Generate refined draft (Tool 4)
    refined_draft = _invoke(_story_llm, IMPROVE_PROMPT(last, instruction), "rewrite_manual")
    
    # 2. Safety Check the refined draft (Tool 3)
    judge = _safe_json(_invoke(_judge_llm, JUDGE_PROMPT(refined_draft), "refine_judge"))
    
    if judge.get("unsafe"):
        # CRITICAL REJECTION: If refinement introduces unsafe content, revert to the last safe story.
        return f"{REFUSAL} I cannot apply that change because it introduces danger, violence, or loss. The current safe story remains unchanged."

    # 3. Apply optional second improvement if the judge provided a hint
    final_story = refined_draft
    if judge.get("hint"):
        final_story = _invoke(_story_llm, IMPROVE_PROMPT(refined_draft, judge["hint"]), "rewrite_post_refine")

    # 4. Save the new safe story
    history = _get_history(session_id)
    
    # Find the last story entry and update its content
    found_and_updated = False
    for msg in reversed(history):
        if isinstance(msg, AIMessage) and msg.content.startswith("[FINAL STORY]"):
            msg.content = f"[FINAL STORY]\n{final_story}"
            found_and_updated = True
            break
            
    if not found_and_updated:
         history.append(AIMessage(content=f"[FINAL STORY]\n{final_story}"))

    _save_history(session_id, history)
    return final_story

def small_chat_reply(session_id: str, user: str) -> str:
    """
    Generates a short, non-story chat reply (Tool 5: Chat Responder).
    """
    # Use context from the last story if available
    ctx = (get_last_story(session_id) or "")[:400]
    
    # Use the Chat Responder tool
    reply = _invoke(_chat_llm, CHAT_PROMPT(ctx, user), "chat_reply").strip()
    
    # Save the AI response to history
    history = _get_history(session_id)
    history.append(AIMessage(content=reply))
    _save_history(session_id, history)
    
    return reply

# ============================================================
# MAIN ROUTER (The Public API)
# ============================================================

def handle_user_message(session_id: str, user_message: str) -> Tuple[str, str, Optional[int]]:
    """
    The main routing function. Uses the LLM Intent Classifier tool for routing.
    
    Returns:
        (response_text, response_type, internal_revision_count)
    """
    has_story = _has_story(session_id)
    
    # --- ROUTING STEP (Uses LLM Tool 1) ---
    intent, instruction = extract_context_and_detect_intent_tool_based(user_message, has_story)
    
    # 1. Save User Message to History (for full context)
    history = _get_history(session_id)
    history.append(HumanMessage(content=user_message))
    _save_history(session_id, history) 

    if intent == "new_story":
        # ROUTE: New Story Pipeline (Tools 2, 3, 4)
        result, suggestions = generate_with_judge_loop(session_id, instruction)
        
        revision_count = 1 if suggestions else 0
        response_type = "refusal" if result == REFUSAL else "story"
        
        return result, response_type, revision_count

    elif intent == "refine":
        # ROUTE: Story Refinement Pipeline (Tool 4)
        response = refine_with_human_feedback(session_id, instruction)
        
        # Check if the refinement function returned the refusal message
        is_refusal = response.startswith(REFUSAL) and "I cannot apply that change" in response
        
        return response, "refusal" if is_refusal else "refinement", None

    else: # intent == "chat"
        # ROUTE: Small Chat Reply (Tool 5)
        response = small_chat_reply(session_id, instruction)
        return response, "chat", None