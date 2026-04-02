# Train Tracker Project Guide

## 1. Project Overview & Aim
**Train Tracker** is an AI-powered Indian Railway Route Planner.
**Aim**: To provide users with intelligent train route suggestions, including direct trains and complex connecting routes (up to 4 legs) when direct options are unavailable. It uses AI to understand natural language queries (e.g., "Plan a trip from Delhi to Mumbai") and to handle station name variations (e.g., "Vaishno Devi" -> "SVDK").

## 2. Technology Stack & Frameworks

### Backend: **Flask** & **LangGraph**
*   **Flask**: A lightweight Python web framework.
    *   *Why?* It's simple, fast to set up, and perfect for creating REST APIs (`/api/smart_query`) that serve the frontend.
*   **LangGraph**: A library for building stateful, multi-actor applications with LLMs.
    *   *Why?* It allows us to model the route planning process as a structured graph (workflow) of steps (Nodes) connected by logic (Edges). This makes the complex logic of intent extraction -> station validation -> route finding -> response generation modular and easier to debug.
*   **OpenAI API**: Uses `gpt-4o-mini`.
    *   *Why?* For natural language understanding (extracting "from" and "to" stations) and for intelligent station name resolution (mapping "home" or "temple" to specific station codes).

### Frontend: **Vanilla HTML/CSS/JS**
*   **HTML5/CSS3**: For structure and styling.
*   **Vanilla JavaScript**: For logic.
    *   *Why?* The frontend requirements are relatively simple (a search box and results display). Using a heavy framework like React would be overkill. Vanilla JS keeps it lightweight and fast.

## 3. Project Structure
```text
Train_Tracker/
├── Langgraph/
│   ├── main.py              # CORE BACKEND: Flask app + LangGraph workflow + Route logic
│   ├── frontend_server.py   # Simple server to host the frontend files (port 3000)
│   ├── config.py            # Configuration loader (env vars, constants)
│   ├── .env                 # Secrets (API Keys)
│   ├── requirements.txt     # Python dependencies
│   └── static/              # FRONTEND ASSETS
│       ├── index.html       # Main UI page
│       ├── style.css        # Styling
│       └── script.js        # Frontend logic (API calls, UI updates)
```

## 4. LangGraph Workflow (The "Brain")
The core logic in `main.py` is structured as a graph.

### **Nodes (The Steps)**
1.  **`extract_intent`**:
    *   **Input**: User query (e.g., "Trains to Goa").
    *   **Action**: Uses OpenAI to parse the text and extract `from` and `to` locations.
    *   **Output**: JSON with intent and raw location strings.
2.  **`convert_stations`**:
    *   **Input**: Raw location strings (e.g., "Goa").
    *   **Action**: Converts names to official Indian Railway Station Codes (e.g., "MAO") using a mix of static mappings and AI. Validates codes against the RailRadar API.
    *   **Output**: Validated Station Codes (`from_code`, `to_code`).
3.  **`find_routes`**:
    *   **Input**: Station codes.
    *   **Action**: The heavy lifter. Searches for direct trains. If none, searches for connecting routes (2, 3, or 4 legs) via major junctions.
    *   **Output**: List of route objects.
4.  **`generate_response`**:
    *   **Input**: Route data.
    *   **Action**: Formats the technical route data into a user-friendly JSON response.
    *   **Output**: Final JSON for the frontend.

### **Edges (The Flow)**
*   `START` -> `extract_intent` -> `convert_stations` -> `find_routes` -> `generate_response` -> `END`
*   The flow is linear: Data passes from one node to the next, accumulating in the `AgentState` dictionary.

## 5. "Legs" Explained
A **Leg** is a single train ride.
*   **Direct Route (1 Leg)**: Station A -> Station B.
*   **Connecting Route (Multiple Legs)**:
    *   **2 Legs**: Station A -> Junction X -> Station B.
    *   **Why?**: Often there is no direct train between two small stations. The code intelligently finds a common "Junction" (like Delhi, Mumbai, Howrah) that connects both.
    *   **How it works**:
        1.  The code has a list of `MAJOR_JUNCTIONS`.
        2.  It checks: Can I go From A -> Junction? AND From Junction -> B?
        3.  If yes, it checks the timings. Is there enough time to change trains (Layover)?
        4.  If the layover is valid (e.g., >20 mins and <12 hours), it creates a valid "2-Leg Route".
    *   The code repeats this logic for 3 legs and 4 legs if simpler routes aren't found, though this takes more time.

## 6. Code Flow & Communication

### **Frontend -> Backend**
1.  **User** types "Delhi to Mumbai" in `index.html`.
2.  **`script.js`** captures this and sends a `POST` request to `http://localhost:5000/api/smart_query`.
    ```javascript
    fetch('http://localhost:5000/api/smart_query', {
        method: 'POST',
        body: JSON.stringify({ query: "Delhi to Mumbai" })
    })
    ```

### **Backend Processing (`main.py`)**
1.  **Flask** receives the request.
2.  It initializes the `AgentState` and invokes the **LangGraph** `agent_graph`.
3.  **LangGraph** runs through the nodes defined above.
4.  **RailRadar API** is called multiple times during `find_routes` to get real train data.
5.  **OpenAI API** is called during `extract_intent` and `convert_stations`.
6.  The final result is returned as JSON.

### **Backend -> Frontend**
1.  **`script.js`** receives the JSON.
2.  It parses the data:
    *   `data.journey`: Trip details.
    *   `data.availableTrains`: List of trains/routes.
3.  It dynamically generates HTML cards for each train and injects them into the page.

## 7. Configuration & Environment
We use a `.env` file to keep secrets safe.
*   **`OPENAI_API_KEY`**: Your secret key to access GPT-4o-mini.
*   *Note*: The URL for the RailRadar API (`https://railradar.in/api/v1`) and the backend `FLASK_PORT` (5000) are hardcoded directly in `main.py` and `frontend_server.py`.

## 8. Performance & Models
*   **Model**: `gpt-4o-mini` is used because it's fast and cheap, which is crucial for a real-time app. It's smart enough to understand "trains from home" but doesn't have the latency of larger models.
*   **Time Taken**:
    *   **Direct Routes**: Very fast (~1-2 seconds).
    *   **Connecting Routes**: Can take **10-30 seconds**.
    *   *Why?* The code has to check *many* combinations. For a 2-leg route, it might check 15 junctions. For each junction, it makes 2 API calls (A->Junction, Junction->B). That's 30+ API calls! The code tries to be smart and stop as soon as it finds 5 good routes.

## 9. End-to-End Walkthrough
**Scenario**: User asks "Help me reach Vaishno Devi from Bangalore".

1.  **Frontend**: Sends query to Backend.
2.  **Backend (Node 1)**: AI sees "Vaishno Devi" and "Bangalore".
3.  **Backend (Node 2)**:
    *   AI converts "Vaishno Devi" -> **SVDK** (Station Code).
    *   AI converts "Bangalore" -> **SBC** (Station Code).
    *   Validates these codes exist via API.
4.  **Backend (Node 3)**:
    *   Checks Direct trains SBC -> SVDK. (Likely none).
    *   Starts **2-Leg Search**. Checks Junctions (e.g., New Delhi - NDLS).
    *   Finds: Train 1 (SBC -> NDLS) arrives at 10:00 AM. Train 2 (NDLS -> SVDK) leaves at 2:00 PM.
    *   Calculates Layover: 4 hours. Status: "Comfortable".
    *   Adds this combination to the list.
5.  **Backend (Node 4)**: Formats this into a clean JSON structure.
6.  **Frontend**: Displays a card showing:
    *   "2-Train Connection via New Delhi"
    *   Train 1 details.
    *   "⏱️ Waiting at New Delhi: 4 hours (Comfortable)"
    *   Train 2 details.
