# 📚 Story Engine AI (Kid-Safe Narrative Generator)

This project is a robust, tool-driven application built on the Gemini API, designed to generate short, warm, and strictly **child-safe** bedtime stories (ages 5–10). It utilizes a multi-step pipeline and specialized LLM tools for intelligent request routing, content generation, automatic safety judging, and secure story refinement.

<img width="1680" height="1050" alt="Screenshot 2025-10-22 at 01 24 38" src="https://github.com/user-attachments/assets/dae37002-f0d9-4b0a-a4c0-98a80fa0093d" />
---

## ✨ Core Features & Tool-Based Architecture

The engine is built around five distinct LLM tools, ensuring predictable, high-quality, and highly secure operation. The use of strict JSON schemas and low-temperature models for critical tasks guarantees reliability.

1.  **Tool-Based Routing (Intent Classifier):** A dedicated, strict LLM determines user intent (`new_story`, `refine`, `chat`) and extracts the precise instruction, replacing error-prone, hardcoded keyword lists.
2.  **Strict Safety Pipeline:** Every generated and refined story is subjected to an internal **Story Evaluator Tool** (Tool 3) for mandatory content review.
3.  **Automatic Refinement:** The system auto-corrects drafts based on internal hints to improve quality (word count, structure) before delivery.
4.  **Persistent Memory:** Utilizes a `JsonMessageHistoryStore` to maintain session history, allowing for contextual chat replies and story refinement over multiple user turns.

---

## 🔒 Strict Safety Policy

The system maintains a **zero-tolerance** policy for negative themes. The **Story Evaluator Tool** (Tool 3) enforces the following rules for all content (initial generation and subsequent refinements):

* **NO** explicit acts of violence, fighting, murder, or injury.
* **NO** concepts of **death, loss, grief, or significant sadness** (even if implied via euphemisms like "tragic loss").
* **NO** intense negative emotions (fear, terror, profound sadness).
* Stories must be **100% positive, warm, and gentle** throughout.

### Security Feature: Refinement Safety Check

To prevent users from introducing unsafe elements through refinement, the system runs all user-requested revisions through the **Story Evaluator Tool**. If the refined content is flagged as unsafe, the system **rejects the change** and keeps the last known safe story, explicitly informing the user of the refusal.

---

## 🛠️ Installation and Setup

### Prerequisites

1.  **Python 3.8+**
2.  **A Gemini API Key**

### Dependencies

Install the required Python packages:

```bash
              pip install langchain-google-genai python-dotenv
              # Note: The code relies on an external 'memory_store.py' file 
              # containing the JsonMessageHistoryStore class.
              
              
              Environment Configuration
              Create a file named .env in the project root to securely store your API key:
              
              Plaintext
              
              # .env file
              GEMINI_API_KEY="YOUR_API_KEY_HERE"
              LANGSMITH_TRACING="false"
              MEMORY_DB_PATH="sessions.json"






