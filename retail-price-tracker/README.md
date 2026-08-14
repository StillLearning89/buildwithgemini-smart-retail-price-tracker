# 🛒 Smart Retail Price Tracker & Comparison Agent

> **One-liner:** An intelligent conversational shopping agent built with Google ADK that searches multi-retailer deals, calculates net out-of-pocket costs with stacked credit card cashback perks, renders itemized receipts with 1-click checkout links, and generates AI promotional videos via Google's Omni model.

<div align="center">

![Smart Retail Price Tracker Agent Demo](demo.gif)

</div>

---

## 🌟 Executive Summary & Key Features

The **Smart Retail Price Tracker & Comparison Agent** transforms online price discovery by solving real-world shopper friction. Rather than displaying raw MSRP sticker prices, the agent calculates true **out-of-pocket costs** by layering local sales tax, shipping fees, store membership discounts, and credit card cashback perks.

### 🚀 Key Features

1. 🔍 **Multi-Platform Deal Search**: Real-time comparison across **Costco**, **Best Buy**, **Amazon**, **Walmart**, **Google Store**, and **Target**.
2. 💳 **Stacked Credit Card Cashback Perks**: Automatically calculates and deducts card rewards:
   - **Prime Visa**: 5% cashback on Amazon
   - **Costco Anywhere Visa**: 2% cashback on Costco
   - **Target Circle Card**: 5% savings on Target
   - **5% Category Cards** *(Chase Freedom Flex / Discover IT)*
   - **2% Flat Cards** *(Citi Double Cash)*
3. 🧾 **Itemized Out-of-Pocket Receipts**: Generates structured collapsible receipts showing Base Price, Store Member Rewards, Card Cashback, Estimated Tax, Shipping, and Final Net Price.
4. 🛒 **1-Click Direct Checkout Links**: Deep links directly to retailer product pages (`[ 🛒 Direct Checkout at Store ](url)`).
5. 🧠 **Cross-Session Memory Bank**: Remembers user zip code, store memberships (Costco Executive, Prime, Google One), card perks, and watchlists across conversations.
6. 📖 **Grounded Retail Policy RAG**: Answers return window, price match guarantee, and warranty questions grounded in official store policy documents.
7. 🎨 **AI Promotional Image Generation**: Creates visual deal graphics and banners using Imagen 3 (`gemini-3.1-flash-lite-image`).
8. 🎬 **Omni Model Video Generation**: Generates 1080p promotional video clips using Google's Omni model (`gemini-omni-flash-preview`) via the Interactions API, saved to Google Cloud Storage.
9. 🪟 **Interactive A2UI Cards**: Renders dynamic micro-UI components (cards, columns, rows) in both ADK Web UI and the custom Cloud Run frontend.

---

## ☁️ Google Cloud Tools & Agent Architecture

| Tool / Technology | Role & Purpose in Project |
| :--- | :--- |
| **Gemini 3.6 Flash** | Core orchestration model driving reasoning, tool dispatch, and structured output formatting. |
| **Vertex AI Agent Runtime (Reasoning Engine)** | Managed serverless hosting target for the ADK agent backend. |
| **Vertex AI Memory Bank** | Long-term memory persistence across user sessions (zip code, memberships, cards). |
| **Vertex AI RAG Engine** | Vector retrieval corpus (`ragCorpora`) over official store policy documentation for grounded answers. |
| **Google Cloud Storage (GCS)** | Public storage bucket (`retail-price-tracker-qwiklabs-gcp-03-47433e0ab402`) for generated videos and deal images. |
| **Google Omni Model (`gemini-omni-flash-preview`)** | Generates short promotional deal videos in the `global` region via the Interactions API. |
| **Imagen 3** | Generates promotional product graphics. |
| **A2UI Protocol** | Standardized JSON protocol (`application/json+a2ui`) for rendering native UI cards in web frontends. |
| **Cloud Run** | Serverless hosting for the FastAPI proxy and responsive web frontend. |

---

## 📁 Project Structure

```text
retail-price-tracker/
├── app/
│   ├── agent.py               # Root ADK agent, tools (search, net calc, Omni video, Imagen, RAG, memory)
│   ├── fast_api_app.py        # Local FastAPI app and A2A server integration
│   ├── a2ui_utils.py          # A2UI callback and metadata wrapper
│   └── app_utils/             # Reasoning engine adapter, A2A routes, and service bindings
├── frontend/                  # FastAPI proxy & responsive HTML/CSS/JS frontend
│   ├── main.py                # A2A proxy server talking to Agent Runtime
│   ├── static/index.html      # Responsive Google Gemini-style Chat UI
│   └── Dockerfile             # Container configuration for Cloud Run
├── docs/                      # Retail policy guide for RAG grounding
├── deployment_metadata.json   # Remote Agent Runtime deployment reference
├── Dockerfile                 # Backend container definition
├── demo.gif                   # Loop demo recording
└── pyproject.toml             # Dependencies (ADK, google-genai, a2a, fastapi)
```

---

## 🛠️ Developer Launch & Deployment Guide

### 1. Prerequisites & Environment Setup

Ensure you have Python 3.12, `uv`, and `gcloud` installed:

```bash
# Clone the repository
git clone https://github.com/StillLearning89/buildwithgemini-smart-retail-price-tracker.git
cd buildwithgemini-smart-retail-price-tracker/retail-price-tracker

# Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate
uv sync
```

Authenticate with Google Cloud:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_GCP_PROJECT_ID
```

---

### 2. Local Backend Execution

Launch the agent backend locally with `agents-cli`:

```bash
# Interactive CLI mode
agents-cli run

# Playground Web UI mode
agents-cli playground
```

Or run the FastAPI app directly:

```bash
PYTHONPATH=. uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000/dev-ui/?app=app` in your browser.

---

### 3. Local Frontend Execution

Run the custom chat UI proxy locally:

```bash
cd frontend
export AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT/locations/us-central1/reasoningEngines/YOUR_ENGINE_ID"
export AGENT_DIRECTORY="app"
python main.py
```
Open `http://localhost:8080` in your browser.

---

### 4. Deploying to Production (Agent Runtime & Cloud Run)

#### Deploy the Agent Backend to Vertex AI Agent Runtime:
```bash
agents-cli deploy --project YOUR_GCP_PROJECT_ID --no-confirm-project
```

#### Deploy the Frontend Proxy to Cloud Run:
```bash
cd frontend
gcloud run deploy retail-price-tracker-frontend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "AGENT_ENGINE_RESOURCE_NAME=projects/YOUR_PROJECT/locations/us-central1/reasoningEngines/YOUR_ENGINE_ID,AGENT_DIRECTORY=app" \
  --project YOUR_GCP_PROJECT_ID
```

---

## 🧪 Evaluation

Run the automated evaluation suite against test query datasets:

```bash
agents-cli eval
```

Sample query verified:
> *"Find me the best price for a 65-inch OLED TV under $1500 including my Costco membership discount and Costco Visa card cashback."*

---

## 📄 License

Demonstration project created for the Build with Gemini workshop.
