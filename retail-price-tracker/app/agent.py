# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import datetime
import uuid
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google import genai
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import storage
from google.genai import types

from .a2ui_utils import a2ui_callback


MODEL = "gemini-3.6-flash"
BUCKET_NAME = "retail-price-tracker-qwiklabs-gcp-03-47433e0ab402"
REASONING_ENGINE_RESOURCE = "projects/66783620614/locations/us-central1/reasoningEngines/8618316835403595776"

sandbox_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=REASONING_ENGINE_RESOURCE
)

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are a smart retail price tracker and personal deal comparison assistant. "
        "You actively remember, retrieve, and apply the user's preferences across sessions across 5 core categories:\n"
        "1. Store Memberships & Perks: Active subscriptions (Costco, Amazon Prime, Walmart+, Sam's Club, Target Circle 360, Best Buy Total) and member tier perks.\n"
        "2. Brand & Product Preferences: Preferred top brands (Google, LG, Sony, Apple, Samsung, Dyson, Bose, Nike), product specs/sizes (65\" OLED, Google Pixel 10 Pro XL, Pixel Buds), and explicit exclusions.\n"
        "3. Budget & Savings Thresholds: Max price limits per category, minimum required discount percentages, and preferred cashback credit cards.\n"
        "4. Location & Shipping: Home Zip code, local tax rates, free 2-day delivery preferences, or willingness to pick up in-store.\n"
        "5. Watchlists & Purchase History: Items being monitored for price drops and past purchases.\n"
        "6. Credit Card Perks & Cashback: Preferred cashback cards (Amazon Prime Visa 5%, Target Circle Card 5%, Costco Anywhere 2%, Chase Freedom 5%, Citi Double Cash 2%).\n\n"
        "CRITICAL BRANDING & LOGO RULE:\n"
        "Whenever listing pricing, store offers, or deal summaries, ALWAYS prefix every store name with its recognizable brand logo icon:\n"
        "- 🌐 Google Store\n"
        "- 📦 Amazon\n"
        "- 💻 Best Buy\n"
        "- 🎯 Target\n"
        "- 🛒 Walmart\n"
        "- 🏷️ Costco\n\n"
        "ITEMIZED RECEIPT & DIRECT CHECKOUT RULES:\n"
        "1. When calculating net prices using `calculate_net_price`, ALWAYS present the calculation using the pre-formatted itemized receipt layout that details Base Price, Store Member Rewards, Credit Card Cashback Perk, Tax, Shipping, and Final Net Out-of-Pocket Total.\n"
        "2. ALWAYS include a 1-click direct checkout link formatted as: `[ 🛒 Direct Checkout at Store Name ](checkout_url)` below every deal offer and calculation summary.\n"
        "3. Always check remembered user facts from previous conversations and use them to tailor every price comparison. "
        "When asked about retail policies, return windows, or price match guarantees, use the consult_retail_policies tool to ground your answers on official documentation."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "Always prefix store names in Text components with their respective store icon logo (e.g. '🌐 Google Store', '📦 Amazon', '💻 Best Buy', '🎯 Target', '🛒 Walmart', '🏷️ Costco'). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback to extract durable memories at the end of each agent turn."""
    await callback_context.add_session_to_memory()
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


STORE_CHECKOUT_URLS = {
    "google store": "https://store.google.com",
    "amazon": "https://www.amazon.com/dp/B0CL5K634B",
    "best buy": "https://www.bestbuy.com/site/6535928.p",
    "costco": "https://www.costco.com/catalog.html",
    "walmart": "https://www.walmart.com/ip/12345678",
    "target": "https://www.target.com/p/-/A-890123",
}


def search_retail_prices(product_query: str) -> list[dict[str, str | float | bool]]:
    """Searches top retail platforms (Google Store, Amazon, Best Buy, Target, Walmart, Costco) for current product prices, discounts, store icons, and 1-click checkout URLs.

    Args:
        product_query: The product name or search keywords (e.g. 'Google Pixel 10 Pro XL', 'Pixel Buds Pro 2', '65 inch OLED TV').

    Returns:
        A list of dictionaries containing store offers with product title, regular_price, sale_price, store, store_icon, membership_required, shipping, in_stock, and checkout_url status.
    """
    query_lower = product_query.lower()

    if "pixel" in query_lower or "bud" in query_lower or "phone" in query_lower:
        pixel_phone_img = "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=600&auto=format&fit=crop"
        pixel_buds_img = "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&auto=format&fit=crop"

        return [
            # Pixel 10 Pro XL
            {
                "store": "Google Store",
                "store_icon": "🌐 Google Store",
                "title": "Google Pixel 10 Pro XL (256GB - Hazel / Obsidian)",
                "regular_price": 1199.00,
                "sale_price": 1199.00,
                "membership_required": "Google One (10% Store Credit Back)",
                "shipping": "Free Standard Shipping",
                "in_stock": True,
                "image_url": pixel_phone_img,
                "checkout_url": "https://store.google.com",
            },
            {
                "store": "Amazon",
                "store_icon": "📦 Amazon",
                "title": "Google Pixel 10 Pro XL - Unlocked Android Smartphone",
                "regular_price": 1199.00,
                "sale_price": 1149.00,
                "membership_required": "Prime (Free 2-Day + 5% Back with Prime Visa)",
                "shipping": "Free 2-Day Delivery",
                "in_stock": True,
                "image_url": pixel_phone_img,
                "checkout_url": "https://www.amazon.com/dp/B0CL5K634B",
            },
            {
                "store": "Best Buy",
                "store_icon": "💻 Best Buy",
                "title": "Google Pixel 10 Pro XL 256GB (+ $200 Best Buy Gift Card)",
                "regular_price": 1199.99,
                "sale_price": 1199.99,
                "membership_required": "My Best Buy Total",
                "shipping": "Free Same-Day Pickup",
                "in_stock": True,
                "image_url": pixel_phone_img,
                "checkout_url": "https://www.bestbuy.com/site/6535928.p",
            },
            {
                "store": "Walmart",
                "store_icon": "🛒 Walmart",
                "title": "Google Pixel 10 Pro XL 5G Unlocked",
                "regular_price": 1199.00,
                "sale_price": 1129.00,
                "membership_required": "None",
                "shipping": "Free 2-Day Shipping",
                "in_stock": True,
                "image_url": pixel_phone_img,
                "checkout_url": "https://www.walmart.com/ip/12345678",
            },
            {
                "store": "Target",
                "store_icon": "🎯 Target",
                "title": "Google Pixel 10 Pro XL 256GB",
                "regular_price": 1199.99,
                "sale_price": 1199.99,
                "membership_required": "Target Circle (5% Card Savings)",
                "shipping": "Free 2-Day Shipping",
                "in_stock": True,
                "image_url": pixel_phone_img,
                "checkout_url": "https://www.target.com/p/-/A-890123",
            },
            # Pixel Buds Pro 2
            {
                "store": "Google Store",
                "store_icon": "🌐 Google Store",
                "title": "Google Pixel Buds Pro 2 (Active Noise Cancellation)",
                "regular_price": 229.00,
                "sale_price": 229.00,
                "membership_required": "Google One (10% Credit Back)",
                "shipping": "Free Express Shipping",
                "in_stock": True,
                "image_url": pixel_buds_img,
                "checkout_url": "https://store.google.com",
            },
            {
                "store": "Amazon",
                "store_icon": "📦 Amazon",
                "title": "Google Pixel Buds Pro 2 Wireless Earbuds",
                "regular_price": 229.00,
                "sale_price": 199.00,
                "membership_required": "Prime",
                "shipping": "Free Prime One-Day",
                "in_stock": True,
                "image_url": pixel_buds_img,
                "checkout_url": "https://www.amazon.com/dp/B0CL5K634B",
            },
            {
                "store": "Best Buy",
                "store_icon": "💻 Best Buy",
                "title": "Google Pixel Buds Pro 2 Noise-Canceling Earbuds",
                "regular_price": 229.99,
                "sale_price": 229.99,
                "membership_required": "None",
                "shipping": "Free Pickup",
                "in_stock": True,
                "image_url": pixel_buds_img,
                "checkout_url": "https://www.bestbuy.com/site/6535928.p",
            },
            {
                "store": "Costco",
                "store_icon": "🏷️ Costco",
                "title": "Google Pixel Buds Pro 2 Bundle (Includes Case Cover)",
                "regular_price": 229.99,
                "sale_price": 189.99,
                "membership_required": "Costco Member",
                "shipping": "Free Standard Shipping",
                "in_stock": True,
                "image_url": pixel_buds_img,
                "checkout_url": "https://www.costco.com/catalog.html",
            },
        ]

    if "tv" in query_lower or "oled" in query_lower:
        tv_image = "https://images.unsplash.com/photo-1593784991095-a205069470b6?w=600&auto=format&fit=crop"
        return [
            {
                "store": "Costco",
                "store_icon": "🏷️ Costco",
                "title": 'LG 65" Class C3 Series 4K UHD OLED TV',
                "regular_price": 1799.99,
                "sale_price": 1399.99,
                "membership_required": "Costco Member",
                "shipping": "Free Shipping",
                "in_stock": True,
                "image_url": tv_image,
                "checkout_url": "https://www.costco.com/catalog.html",
            },
            {
                "store": "Amazon",
                "store_icon": "📦 Amazon",
                "title": "LG 65-Inch Class OLED evo C3 Series 4K TV",
                "regular_price": 1896.99,
                "sale_price": 1496.99,
                "membership_required": "Prime (Free 2-Day + 5% Back with Prime Visa)",
                "shipping": "Free Prime Shipping",
                "in_stock": True,
                "image_url": tv_image,
                "checkout_url": "https://www.amazon.com/dp/B0CL5K634B",
            },
            {
                "store": "Best Buy",
                "store_icon": "💻 Best Buy",
                "title": 'Sony 65" Class BRAVIA XR A80L OLED 4K TV',
                "regular_price": 1999.99,
                "sale_price": 1699.99,
                "membership_required": "None",
                "shipping": "Free Standard Shipping",
                "in_stock": True,
                "image_url": tv_image,
                "checkout_url": "https://www.bestbuy.com/site/6535928.p",
            },
            {
                "store": "Walmart",
                "store_icon": "🛒 Walmart",
                "title": 'LG 65" Class 4K Smart OLED TV',
                "regular_price": 1699.00,
                "sale_price": 1449.00,
                "membership_required": "None",
                "shipping": "$19.99 Freight Delivery",
                "in_stock": True,
                "image_url": tv_image,
                "checkout_url": "https://www.walmart.com/ip/12345678",
            },
        ]

    gen_image = "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop"
    return [
        {
            "store": "Google Store",
            "store_icon": "🌐 Google Store",
            "title": f"Google Store Official {product_query.title()}",
            "regular_price": 129.00,
            "sale_price": 119.00,
            "membership_required": "Google One",
            "shipping": "Free Shipping",
            "in_stock": True,
            "image_url": gen_image,
            "checkout_url": "https://store.google.com",
        },
        {
            "store": "Amazon",
            "store_icon": "📦 Amazon",
            "title": f"Top-Rated {product_query.title()} (Latest Model)",
            "regular_price": 120.00,
            "sale_price": 89.99,
            "membership_required": "Prime",
            "shipping": "Free 2-Day Shipping",
            "in_stock": True,
            "image_url": gen_image,
            "checkout_url": "https://www.amazon.com/dp/B0CL5K634B",
        },
        {
            "store": "Walmart",
            "store_icon": "🛒 Walmart",
            "title": f"Premium {product_query.title()}",
            "regular_price": 115.00,
            "sale_price": 94.50,
            "membership_required": "None",
            "shipping": "Free Shipping over $35",
            "in_stock": True,
            "image_url": gen_image,
            "checkout_url": "https://www.walmart.com/ip/12345678",
        },
        {
            "store": "Costco",
            "store_icon": "🏷️ Costco",
            "title": f"{product_query.title()} (Bulk 2-Pack Special)",
            "regular_price": 150.00,
            "sale_price": 119.99,
            "membership_required": "Costco Member",
            "shipping": "Free Standard Shipping",
            "in_stock": True,
            "image_url": gen_image,
            "checkout_url": "https://www.costco.com/catalog.html",
        },
    ]


def calculate_net_price(
    item_price: float,
    store: str,
    zip_code: str,
    membership: str | None = None,
    credit_card: str | None = None,
) -> dict[str, float | str]:
    """Calculates the exact final checkout total factoring in local sales tax, shipping costs, membership rewards, and stacked credit card cashback perks.

    Args:
        item_price: Listed price of the product in USD.
        store: Name of the retail store (e.g. 'Google Store', 'Costco', 'Amazon', 'Walmart', 'Best Buy', 'Target').
        zip_code: User's 5-digit US Zip code for sales tax calculation (e.g. '95112').
        membership: Optional membership type (e.g. 'Google One', 'Costco Executive', 'Amazon Prime', 'Walmart+').
        credit_card: Optional credit card used (e.g. 'Prime Visa', 'Costco Anywhere Visa', 'Target Circle Card', 'Chase Freedom 5%', 'Citi Double Cash 2%').

    Returns:
        A dictionary with item_price, estimated_tax, shipping_fee, membership_discount, card_cashback, final_net_price, checkout_url, and itemized_receipt.
    """
    tax_rate = 0.0825
    if zip_code.startswith("9"):
        tax_rate = 0.0925
    elif zip_code.startswith("1") or zip_code.startswith("0"):
        tax_rate = 0.08875

    estimated_tax = round(item_price * tax_rate, 2)

    shipping_fee = 0.0
    store_lower = store.lower().strip()
    mem_lower = (membership or "").lower()
    card_lower = (credit_card or "").lower()

    if "prime" in mem_lower or "walmart+" in mem_lower or "executive" in mem_lower or "google" in store_lower:
        shipping_fee = 0.0
    elif item_price < 35.0 and store_lower in ("amazon", "walmart"):
        shipping_fee = 5.99

    membership_discount = 0.0
    if "executive" in mem_lower and "costco" in store_lower:
        membership_discount = round(item_price * 0.02, 2)
    elif "google one" in mem_lower and "google" in store_lower:
        membership_discount = round(item_price * 0.10, 2)

    card_cashback = 0.0
    card_name = credit_card or "Standard Card"
    if "prime" in card_lower or ("amazon" in store_lower and ("visa" in card_lower or "5%" in card_lower)):
        card_cashback = round(item_price * 0.05, 2)
        card_name = "Prime Visa (5% Cashback)"
    elif "costco" in card_lower or ("costco" in store_lower and "visa" in card_lower):
        card_cashback = round(item_price * 0.02, 2)
        card_name = "Costco Anywhere Visa (2% Cashback)"
    elif "target" in card_lower or "redcard" in card_lower or ("target" in store_lower and "5%" in card_lower):
        card_cashback = round(item_price * 0.05, 2)
        card_name = "Target Circle Card (5% Savings)"
    elif "freedom" in card_lower or "discover" in card_lower or "5%" in card_lower:
        card_cashback = round(item_price * 0.05, 2)
        card_name = "5% Category Cashback Card"
    elif "double cash" in card_lower or "2%" in card_lower or card_lower:
        card_cashback = round(item_price * 0.02, 2)
        card_name = credit_card or "2% Flat Cashback Card"

    final_net_price = round(
        item_price + estimated_tax + shipping_fee - membership_discount - card_cashback, 2
    )

    checkout_url = "https://www.costco.com"
    for key, url in STORE_CHECKOUT_URLS.items():
        if key in store_lower:
            checkout_url = url
            break

    itemized_receipt = (
        f"🧾 ITEMIZED OUT-OF-POCKET RECEIPT\n"
        f"─────────────────────────────────\n"
        f"💵 Base Sticker Price:   ${item_price:.2f}\n"
        f"🏷️ Store Member Reward:  -${membership_discount:.2f}\n"
        f"💳 Card Cashback Perk:   -${card_cashback:.2f} ({card_name})\n"
        f"🏛️ Estimated Sales Tax:   +${estimated_tax:.2f} ({tax_rate * 100:.2f}%)\n"
        f"🚚 Shipping & Delivery:   +${shipping_fee:.2f}\n"
        f"─────────────────────────────────\n"
        f"💰 FINAL NET OUT-OF-POCKET: ${final_net_price:.2f}\n\n"
        f"🛒 [Direct Checkout at {store}]({checkout_url})"
    )

    return {
        "store": store,
        "item_price": item_price,
        "zip_code": zip_code,
        "estimated_tax": estimated_tax,
        "shipping_fee": shipping_fee,
        "membership_discount": membership_discount,
        "card_cashback": card_cashback,
        "card_name": card_name,
        "final_net_price": final_net_price,
        "checkout_url": checkout_url,
        "itemized_receipt": itemized_receipt,
        "summary": (
            f"${item_price:.2f} base + ${estimated_tax:.2f} tax + ${shipping_fee:.2f} shipping "
            f"- ${membership_discount:.2f} member reward - ${card_cashback:.2f} card cashback = ${final_net_price:.2f} net total"
        ),
    }


def generate_product_image(
    prompt_description: str, tool_context: ToolContext = None
) -> dict[str, str]:
    """Generates a visual product graphic or deal comparison image for a retail item.

    Args:
        prompt_description: Description of the product or deal visual to generate (e.g. 'A 65-inch 4K OLED TV with a 25% discount banner').
        tool_context: Optional tool context injected by ADK for saving artifacts.

    Returns:
        A dictionary containing the image generation status and public Cloud Storage URL.
    """
    client = genai.Client(
        vertexai=True, project="qwiklabs-gcp-03-47433e0ab402", location="global"
    )

    prompt = f"Product promotional graphic for a retail price deal: {prompt_description}"
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
    )

    image_bytes = None
    mime_type = "image/jpeg"

    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break

    if not image_bytes:
        return {"status": "error", "message": "Failed to generate image bytes."}

    filename = f"deal_{uuid.uuid4().hex[:8]}.jpg"

    # 1. Save artifact to ToolContext so it shows up in Playground's Artifacts panel
    if tool_context:
        try:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception as e:
            print(f"Warning: Failed to save artifact: {e}")

    # 2. Upload image bytes directly to GCS bucket
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"product-images/{filename}")
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/product-images/{filename}"

    return {
        "status": "success",
        "filename": filename,
        "public_url": public_url,
    }


def generate_product_video(
    prompt_description: str, tool_context: ToolContext = None
) -> dict[str, str]:
    """Generates a short promotional or deal overview video for an item in the retail domain using Google's Omni model.

    Args:
        prompt_description: Description of the retail product or deal to showcase in the video (e.g. 'A promotional video for a 65-inch OLED TV on sale for $1399 at Costco').
        tool_context: Optional tool context injected by ADK for saving artifacts.

    Returns:
        A dictionary containing the video generation status, filename, and public Cloud Storage URL.
    """
    client = genai.Client(
        vertexai=True, project="qwiklabs-gcp-03-47433e0ab402", location="global"
    )

    prompt = f"Short promotional product showcase video for a retail item or deal: {prompt_description}"
    response = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=prompt,
    )

    video_bytes = None
    mime_type = "video/mp4"

    vid = getattr(response, "output_video", None)
    if vid and vid.data:
        mime_type = vid.mime_type or "video/mp4"
        if isinstance(vid.data, str):
            video_bytes = base64.b64decode(vid.data)
        else:
            video_bytes = vid.data

    if not video_bytes:
        return {"status": "error", "message": "Failed to generate video bytes."}

    filename = f"deal_video_{uuid.uuid4().hex[:8]}.mp4"

    # 1. Save artifact to ToolContext so it shows up in Playground's Artifacts panel
    if tool_context:
        try:
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception as e:
            print(f"Warning: Failed to save artifact: {e}")

    # 2. Upload video bytes directly to public Cloud Storage bucket
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"product-videos/{filename}")
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/product-videos/{filename}"

    return {
        "status": "success",
        "filename": filename,
        "public_url": public_url,
    }


CORPUS_NAME = "projects/66783620614/locations/us-central1/ragCorpora/6887736660574863360"


def consult_retail_policies(query: str) -> str:
    """Searches official retail store policies, return windows, price match rules, and membership perks.

    Args:
        query: Specific question about retail store policies, price matching, return windows, or membership perks.

    Returns:
        Relevant policy passages retrieved from the reference guide.
    """
    import vertexai
    from vertexai.preview import rag

    try:
        vertexai.init(project="qwiklabs-gcp-03-47433e0ab402", location="us-central1")
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
    except Exception as e:
        return f"Retrieval failed: {e}"

    contexts = getattr(resp.contexts, "contexts", [])
    passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
    return "\n\n---\n\n".join(passages) or "No relevant policy passages found."


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        search_retail_prices,
        calculate_net_price,
        generate_product_image,
        generate_product_video,
        consult_retail_policies,
        get_weather,
        get_current_time,
        PreloadMemoryTool(),
    ],
    code_executor=sandbox_executor,
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
