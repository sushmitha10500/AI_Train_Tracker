# 🚆 AI‑Powered Indian Railway Route Planner

An intelligent **Indian Railway route planning system** that uses **OpenAI (GPT‑4o‑mini)** and **LangGraph** to understand natural language queries and return optimal train routes — including **direct and multi‑leg connections (up to 4 legs)** — with smart recommendations and layover analysis.

---

## 📌 Table of Contents

1. Project Overview
2. Key Objectives
3. Features
4. Tech Stack
5. System Architecture
6. Project Structure
7. LangGraph Workflow (Core Logic)
8. Detailed Node‑wise Explanation
9. State Management (`AgentState`)
10. Route & Leg Logic Explained
11. API Endpoints
12. Frontend–Backend Interaction
13. End‑to‑End Execution Flow
14. Performance Considerations
15. Setup & Installation
16. Running the Project
17. Future Enhancements
18. License

---

## 1️⃣ Project Overview

**Train Tracker** is an AI‑powered route planning application for **Indian Railways**. Instead of forcing users to know exact station names or codes, it allows **natural language queries** like:

> "Help me travel from Vaishno Devi to Bangalore"

The system intelligently:

* Understands intent
* Resolves station names
* Finds direct or connecting routes
* Analyzes layovers
* Recommends the best journey option

---

## 2️⃣ Key Objectives

* Remove complexity of Indian Railway station codes
* Support complex journeys where direct trains don’t exist
* Demonstrate **LangGraph‑based orchestration** of LLM workflows
* Provide production‑style architecture for AI applications

---

## 3️⃣ ✨ Features
 
* 🤖 **AI‑Powered Intent Extraction** (from/to locations)
* 🚉 **Smart Station Resolution** (handles temples, cities, aliases)
* 🔄 **Multi‑Leg Route Discovery** (1–4 legs)
* ⏱️ **Layover Feasibility Analysis**
* 🎯 **AI‑Generated Route Recommendations**
* 🔁 **Fallback to Nearby Stations**
* ⚡ **Optimized API Calls & Early Stopping**
* 🛡️ **Environment‑based Secure Configuration**

---

## 4️⃣ 🛠️ Technology Stack

### Backend

* **Python**
* **Flask** – REST API
* **LangGraph** – Workflow orchestration
* **OpenAI (GPT‑4o‑mini)** – NLP & reasoning
* **RailRadar API** – Live train data

### Frontend

* HTML5
* CSS3
* Vanilla JavaScript

---

## 5️⃣ 🧠 System Architecture

```
User → Frontend → Flask API → LangGraph Workflow
                          ↓
                  OpenAI + Railway APIs
                          ↓
                     JSON Response
```

LangGraph acts as the **brain**, coordinating multiple AI and API‑driven steps in a deterministic, debuggable workflow.

---

## 6️⃣ 📁 Project Structure

```
Train_Tracker/
├── Langgraph/
│   ├── main.py              # Flask app + LangGraph workflow
│   ├── frontend_server.py   # Serves frontend (port 3000)
│   ├── config.py            # Environment & constants
│   ├── .env                 # API keys (ignored in git)
│   ├── requirements.txt
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── script.js
```

---

## 7️⃣ 🔗 LangGraph Workflow (Core Logic)

LangGraph models the entire reasoning process as a **stateful directed graph**.

### Workflow Diagram

```
START
  ↓
extract_intent
  ↓
convert_stations
  ↓
find_routes
  ↓
generate_response
  ↓
END
```

Each node modifies a shared state object (`AgentState`).

---

## 8️⃣ 🧩 Node‑by‑Node Explanation

### 🔹 1. `extract_intent`

**Purpose**: Understand user intent and extract locations

* Uses GPT to parse the query
* Extracts:

  * `intent` (usually `find_trains`)
  * `from`, `to` locations

Example:

```
"Find trains from Goa to Varanasi"
→ { from: "Goa", to: "Varanasi" }
```

---

### 🔹 2. `convert_stations`

**Purpose**: Convert human names → official station codes

Capabilities:

* City → station code
* Temple → nearest station
* Misspellings & aliases

Example:

```
Vaishno Devi → SVDK
Mumbai → BCT / CSTM
```

Fallback logic:

* Suggests nearby stations
* Validates via Railway API

---

### 🔹 3. `find_routes`

**Purpose**: Discover possible train journeys

Search Strategy:

1. Direct trains
2. 2‑Leg routes (via major junctions)
3. 3‑Leg routes
4. 4‑Leg routes (last resort)

Smart checks:

* Layover between 20 min – 12 hrs
* Stops after finding enough valid routes

---

### 🔹 4. `generate_response`

**Purpose**: Convert raw route data into user‑friendly JSON

Adds:

* Route summaries
* Layover recommendations
* AI‑chosen best option

Layover Labels:

* 🔴 Tight (<30m)
* 🟠 Moderate
* 🟢 Comfortable
* 🔵 Long

---

## 9️⃣ 📦 State Management (`AgentState`)

```python
class AgentState(TypedDict):
    query: str
    intent: str
    extracted_params: Dict[str, Any]
    api_results: Dict[str, Any]
    final_response: str
    errors: List[str]
```

### Why this matters:

* Shared memory across nodes
* Easy debugging
* Deterministic execution
* No hidden state

---

## 🔟 🚦 Route & Leg Logic Explained

### What is a Leg?

* **1 Leg** = One train journey

### Examples

* **Direct**: A → B
* **2 Legs**: A → X → B
* **3 Legs**: A → X → Y → B

Major junctions are prioritized (NDLS, HWH, MAS, SBC, BCT).

---

## 1️⃣1️⃣ 📡 API Endpoints

### Smart Query

```
POST /api/smart_query
{
  "query": "Find trains from Delhi to Goa"
}
```

### Health

```
GET /health
```

---

## 1️⃣2️⃣ 🔁 Frontend ↔ Backend Flow

1. User submits query
2. JavaScript sends POST request
3. Flask invokes LangGraph
4. LangGraph runs nodes sequentially
5. Final JSON returned
6. UI dynamically renders routes

---

## 1️⃣3️⃣ 🔍 End‑to‑End Example

**Query**:

```
Help me reach Vaishno Devi from Bangalore
```

**Flow**:

* AI extracts locations
* Converts to `SBC → SVDK`
* Finds route via `NDLS`
* Calculates 4‑hour layover
* Recommends best journey

---

## 1️⃣4️⃣ ⚡ Performance Considerations

* GPT‑4o‑mini chosen for speed + cost
* Early stopping after enough routes
* Junction prioritization

Typical Time:

* Direct: 1–2 sec
* Multi‑leg: 10–30 sec

---

## 1️⃣5️⃣ ⚙️ Setup & Installation

```bash
pip install -r requirements.txt
```

Create `.env`:

```
OPENAI_API_KEY=your_key_here
```

---

## 1️⃣6️⃣ ▶️ Running the Project

```bash
python main.py
```

Backend:

```
http://localhost:5000
```

Frontend:

```
http://localhost:3000
```

---

## 1️⃣7️⃣ 🚀 Future Enhancements

* Fare prediction
* Seat availability
* User preferences (fastest vs cheapest)
* Graph branching & parallel nodes
* Caching layer

---

## 1️⃣8️⃣ 📜 License

Educational & demonstration use only.

---

## 🙌 Contributing

Pull requests are welcome.

---

## 📧 Support

Open an issue for questions or bugs.

---

### ⭐ If this project helped you understand LangGraph + AI orchestration, give it a star on GitHub!

