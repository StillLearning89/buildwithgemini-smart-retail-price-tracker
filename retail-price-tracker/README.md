# 🛒 Smart Retail Price Tracker & Comparison Agent

> **One-liner:** A conversational agent that helps shoppers find the best deals, compare prices across top retail platforms (Amazon, Walmart, Costco, Best Buy, Google Store), calculate net checkout prices with memberships & taxes, and generate visual deal assets.

<div align="center">

![Smart Retail Price Tracker Agent Demo](demo.gif)

</div>

---

## 🌟 Overview

The **Smart Retail Price Tracker & Comparison Agent** is built on Google Cloud's **Agent Development Kit (ADK)** and deployed to **Agent Runtime**. It serves as an intelligent shopping companion that goes beyond basic price searching by accounting for store membership discounts (e.g. Costco Member, Amazon Prime), taxes, shipping costs, and price match policies.

In addition to calculating net savings, the agent generates promotional deal graphics and AI product videos powered by Google's **Omni Model** (`gemini-omni-flash-preview`).

---

## ✨ Key Features

- 🏷️ **Multi-Platform Price Search & Comparison**: Searches deals across top retailers (Costco, Best Buy, Amazon, Walmart, Google Store).
- 🧮 **Net Price Calculator**: Calculates net checkout cost taking into account user memberships, estimated sales tax, shipping fees, and store discounts.
- 🪟 **Interactive A2UI Cards & Comparison Tables**: Generates rich Agent-Driven UI cards and side-by-side product comparison tables directly in the chat UI.
- 🖼️ **Generative Promotional Image Graphics**: Creates visual deal cards and product banners using Imagen 3.
- 🎬 **AI Promotional Video Generation**: Generates 1080p promotional video clips for deals using Google's Omni model (`gemini-omni-flash-preview`) via the Interactions API, saving artifacts and serving them via public Cloud Storage URLs.
- 🧠 **Cross-Session Shopper Memory**: Remembers user store memberships (e.g., Prime, Costco), preferred brands, budget limits, and price alert thresholds.
- 📖 **Grounded Policy RAG**: Answers questions about store return windows, price match guarantees, and warranty terms grounded in retail policy documents.

---

## ☁️ Google Cloud Infrastructure & Tools Used

| Tool / Technology | Purpose & Usage in Agent |
| :--- | :--- |
| **Vertex AI Memory Bank** | Manages cross-session long-term memory for shopper profiles, store memberships, and budget preferences. |
| **Google Cloud Storage (GCS)** | Public bucket storage (`retail-price-tracker-qwiklabs-gcp-03-47433e0ab402`) for generated product videos and deal graphics. |
| **Firestore** | Persistent structured storage for tracked deals and store catalog records. |
| **Vertex AI RAG Engine** | Grounded retrieval for retail store return windows and price match policies. |
| **Google Omni Model (`gemini-omni-flash-preview`)** | Generates short promotional deal videos in the `global` region via the Interactions API. |
| **Imagen 3** | Generates visual promotional graphics and deal summary cards. |
| **A2UI (Agent-Driven UI)** | Emits structured JSON (`application/json+a2ui`) to render dynamic interactive cards and tables. |
| **ADK & Agent Runtime** | Core agent reasoning loop deployed via `agents-cli`. |

---

## 📁 Project Structure

```text
retail-price-tracker/
├── app/
│   ├── agent.py               # Root agent, tools (video, image, search, math), memory & system prompt
│   ├── fast_api_app.py        # FastAPI server & ADK Web UI
│   └── app_utils/             # A2UI helpers, memory tools, and RAG integration
├── frontend/                  # FastAPI proxy & custom web chat frontend
├── docs/                      # Retail policy documents for RAG grounding
├── demo.gif                   # Loop demo recording
├── retail_price_tracker_demo.webm # Original screen recording
└── pyproject.toml             # Python dependencies
```

---

## 🚀 Quick Start

### 1. Installation

Ensure you have `uv` and `google-agents-cli` installed:

```bash
# Install dependencies
agents-cli install
```

### 2. Local Development & Testing

Launch the local ADK Playground web server:

```bash
agents-cli playground
```

Or run the FastAPI app directly:

```bash
python -m app.fast_api_app
```

Navigate to `http://localhost:8000/dev-ui/?app=app` to interact with the agent.

---

## 🧪 Evaluation

To run evaluations against the sample dataset:

```bash
agents-cli eval
```

Sample query tested:
> *"Find me the best price for a 65-inch OLED TV under $1500 including my Costco membership discount."*

---

## 📄 License

Demonstration project created for the Build with Gemini workshop.
