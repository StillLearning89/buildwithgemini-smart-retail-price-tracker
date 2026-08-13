# My agent: Smart Retail Price Tracker & Comparison Agent
One-liner: A conversational agent that helps shoppers find the best deals and compare prices across top retail platforms (Amazon, Walmart, Costco, etc.) with a catalog of product deals.

Tool coverage:
- Memory: Remembers user store memberships (Prime, Costco Member), preferred brands, budget limits, and price alert thresholds
- Tools: Searches and compares prices across platforms, calculates total cost (tax + shipping + discounts)
- Catalog/UI: Product comparison cards and side-by-side deal comparison tables
- Image gen: Generates visual deal summaries or product comparison graphics
- Sandbox: Computes total cart savings, unit prices (e.g., $ / oz), and price change percentages

Core rails (everyone): memory, tools, eval, deploy, frontend
My stretch menu (pick later): A2UI card/table catalog, code sandbox for unit price math, image generation for deal summaries
First eval question: "Find me the best price for a 65-inch OLED TV under $1500 including my Costco membership discount."
