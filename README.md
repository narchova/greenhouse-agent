# Greenhouse Assistant 🌿

An intelligent, multimodal plant care and inventory management agent built with Google Agent Development Kit (ADK), deployed on Vertex AI Agent Engine, and paired with an interactive chat frontend.

---

## 🌟 What the Agent Does

The Greenhouse Assistant manages indoor plants, diagnoses care needs, answers botany questions, and visually illustrates plant varieties.

### Implemented Capabilities & Tools

* **🌱 Firestore Plant Inventory:**
  * `list_plants`: Lists greenhouse plants stored in Google Cloud Firestore.
  * `search_plants_by_light`: Finds plants by lighting conditions (`low`, `indirect`, `bright`).
  * `get_plant_details`: Fetches plant species, care routines, and current status.
  * `add_plant`: Records new plant inventory into Firestore.
  * `log_plant_watering`: Updates the last watered timestamp and resets watering schedules.
* **🧠 Cross-Session Memory (Vertex AI Memory Bank):**
  * Uses `PreloadMemoryTool` and Vertex AI Memory Bank (`VertexAiMemoryBankService`) to recall user gardening preferences, plant collections, and care routines across conversations.
* **🖼️ Multimodal Image Generation:**
  * `generate_plant_image`: Generates high-quality plant illustrations using `gemini-3.1-flash-lite-image` in the global region.
  * Automatically stores images as session artifacts (`tool_context.save_artifact`) and uploads them to a public Google Cloud Storage bucket (`gs://greenhouse-plants-qwiklabs-gcp-03-2deba0eddfc5`).
* **🎬 Multimodal Video Generation:**
  * `generate_plant_video`: Generates short plant videos using Google's Omni model (`gemini-omni-flash-preview`) via Vertex AI Interactions API. Saves as artifacts and uploads to Cloud Storage.
* **🗺️ Location & Sourcing Tools:**
  * `geocode_address` & `find_nearby_places`: Uses Google Maps Geocoding & Places (New) APIs to find local plant nurseries and greenhouse supply stores.
* **🔬 Botanical Taxonomy:**
  * `lookup_species_taxonomy`: Queries the GBIF (Global Biodiversity Information Facility) API for taxonomic classification.
* **💻 Python Code Execution:**
  * `AgentEngineSandboxCodeExecutor`: Safely calculates customized fertilizer dilution ratios and soil volume math in an Agent Engine secure Python sandbox.
* **✨ Rich UI Cards (A2UI):**
  * Emits Agent-to-UI (`A2UI` v0.8 Basic Catalog) components for rendering rich cards, badges, columns, and images directly in the chat interface.

---

## 🏗️ Architecture

```
User Browser
    │
    ▼
FastAPI Proxy (frontend/main.py)
    │  (A2A Protocol / google.genai.Client)
    ▼
Vertex AI Agent Engine (Remote Runtime)
    ├── Gemini 3.8 Flash (Reasoning & Orchestration)
    ├── Google Cloud Firestore (Plant Inventory & Watering Logs)
    ├── Google Cloud Storage (Plant Image & Video CDN)
    ├── Vertex AI Memory Bank (Long-term Memory)
    ├── Vertex AI Sandbox (Python Code Execution)
    └── External APIs (Maps Places/Geocoding, GBIF Taxonomy)
```

---

## 🚀 Running Locally

### 1. Prerequisites
* Python 3.10+
* Google Cloud SDK (`gcloud`) authenticated to your project with Vertex AI and Firestore permissions:
  ```bash
  gcloud auth application-default login
  ```

### 2. Run the Agent Locally (ADK Playground)
Navigate to the project root and start the ADK web development server:
```bash
uv run adk web . --port 8000 --reload_agents
```

### 3. Run the Custom Chat Frontend
In a separate terminal, navigate to the `frontend/` directory and run the FastAPI server:
```bash
cd frontend
pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_ID>/locations/<REGION>/reasoningEngines/<ENGINE_ID>"
export AGENT_DIRECTORY="app"
python main.py
```
Open your browser to the local port indicated in the terminal (default port 8080).

---

## 📦 Deployment

### Deploy Agent Engine
```bash
agents-cli deploy --agent-directory app
```

### Deploy Frontend to Cloud Run
```bash
gcloud run deploy greenhouse-frontend \
  --source frontend/ \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_ID>/locations/<REGION>/reasoningEngines/<ENGINE_ID>",AGENT_DIRECTORY="app"
```
