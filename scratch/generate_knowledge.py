import json
from pathlib import Path

out_dir = Path("chatbot/src/data")
out_dir.mkdir(parents=True, exist_ok=True)

chunks = [
    {
        "id": "discount_july_summary",
        "title": "July 2026 Sold Share Discount History & Portfolio Metrics",
        "category": "Pricing & Discounts",
        "source_file": "Discount Price.xlsx",
        "source_sheet": "Sheet1",
        "content": """Month of July 2026 Sold Share Discount History & Portfolio Metrics:
- Total Sales Deals Recorded: 115 client purchases.
- Total Sold Shares: 195 hotel share units.
- Cumulative Original (Gross) Value: 54,730,000 BDT.
- Cumulative Discount Granted: 14,940,000 BDT.
- Average Company Discount Percentage: 27.30%.
- Cumulative Net Contracted Sales Price: 39,790,000 BDT.
- Total Deposit Collected up to July 2026: 9,348,450 BDT.
- Remaining Customer Dues to be Collected: 30,441,550 BDT.
- August 2026 Follow-up Deposited: 2,532,200 BDT.
- Division Focus: All transactions were managed under the Corporate Division across executives like Jafor, Champa, Jakaria, Purnima, Susmita, Mizan, Salehin, Juthy, Dipankar, Sameer, AlAmin, Mawsi, Arin, Abu Shama.""",
        "keywords": ["discount", "july", "shares sold", "dues", "deposit", "sales price", "original price", "corporate division", "39790000", "14940000", "54730000"]
    },
    {
        "id": "share_types_pricing_catalog",
        "title": "Official Hotel Share Types, List Prices, and Standard Discount Ranges",
        "category": "Pricing & Discounts",
        "source_file": "Discount Price.xlsx",
        "source_sheet": "Sheet1",
        "content": """Sunset Kuakata Hotel & Resort Ltd. Share Product Catalog & Pricing Structure:
1. Type 1 Share (Single Suite Share Unit):
   - Gross List Price: 250,000 BDT.
   - Standard Approved Discount Range: 15% to 40% (37,500 to 100,000 BDT discount).
   - Typical Net Sale Price: 150,000 to 212,500 BDT.
   - Entry Booking Token: Starting from 1,000 BDT to 50,000 BDT deposit with remaining on EMI installments.
2. Type 2 Share (Two-Share Unit / Double Suite Fraction):
   - Gross List Price: 500,000 BDT.
   - Typical Approved Discount: ~26% (130,000 BDT discount).
   - Net Sale Price: 370,000 BDT.
   - Full cash payment or staged milestones.
3. Type 3 Share (Three-Share Block / Deluxe Suite):
   - Gross List Price: 720,000 to 940,000 BDT.
   - Approved Discount Range: 23.6% to 30.85% (170,000 to 290,000 BDT discount).
   - Net Sale Price: 550,000 to 705,000 BDT.
4. Type 10 Share (10-Share High-Net-Worth Investor Block):
   - Gross List Price: 2,200,000 BDT.
   - Approved Bulk Discount: 27.27% (600,000 BDT discount).
   - Net Sale Price: 1,600,000 BDT (Deposit: 100,000 BDT with 1,500,000 BDT dues).""",
        "keywords": ["pricing", "types", "type 1", "type 2", "type 3", "type 10", "suite share", "deluxe share", "list price", "discount range", "250000", "500000", "940000", "2200000"]
    },
    {
        "id": "september_2026_executive_kpis",
        "title": "September 2026 Corporate Sales Operations & Target Achievement Audit",
        "category": "Executive Performance",
        "source_file": "Estimated Budget -September 26.xlsx",
        "source_sheet": "30.9.26",
        "content": """September 2026 Overall Corporate Sales Results (as of 30.09.2026):
- Total Management Target: 46,500,000 BDT assigned across the sales force.
- Total Achieved New Sales: 8,249,000 BDT.
- Overall Achievement Rate: 17.74% (calculated as Achieved / Target).
- Total Collection (New Sales Deposits + EMI Collections): 13,839,450 BDT.
- Total Outstanding Dues for the Month: 38,251,000 BDT.
- Total Shares Sold in September: 25 shares.
- Total Token Bookings in September: 7 tokens.
- Total Active Sales Executives: 36 personnel.
- Executives Met or Exceeded 100% Target: 0 (No executive achieved 100% of individual budget).
- Executives with Zero Sales Achieved: 23 out of 36 executives (63.9% of sales team recorded 0 BDT in new sales).
- Sales Concentration: Top 10 executives accounted for over 92% of all achieved sales volume.""",
        "keywords": ["september", "target", "achieved", "collection", "achievement rate", "emi", "tokens", "sales performance", "46500000", "8249000", "13839450"]
    },
    {
        "id": "september_top_executives",
        "title": "Top Performing Sales Executives & Leaders in September 2026",
        "category": "Executive Performance",
        "source_file": "Estimated Budget -September 26.xlsx",
        "source_sheet": "30.9.26",
        "content": """Top Sales Performer Rankings (September 2026):
1. Top Team Leader 1 (Exec-01 / Team Leader):
   - Management Target: 5,000,000 BDT
   - Achieved Amount: 1,750,000 BDT (35.0% achievement rate)
   - Highest absolute revenue contributor in the company.
2. Top Team Leader 2 (Exec-02 / Team Leader):
   - Management Target: 4,000,000 BDT
   - Achieved Amount: 1,450,000 BDT (36.25% achievement rate).
3. Leading Sales Executive (Exec-03 / Executive):
   - Management Target: 1,500,000 BDT
   - Achieved Amount: 1,000,000 BDT (66.67% achievement rate - highest percentage among major contributors).
4. Senior Executive (Exec-04 / Executive):
   - Management Target: 2,000,000 BDT
   - Achieved Amount: 850,000 BDT (42.5% achievement rate).
5. Sales Coordinator (Exec-05 / Coordinator):
   - Management Target: 1,000,000 BDT
   - Achieved Amount: 650,000 BDT (65.0% achievement rate).
Operational Observation: Sales performance is highly concentrated among team leaders and top 5 producers. Branch leadership consists of Hasib, Gazi Sir, Dipankar, Soumen, Nahid, Mizan, Mou, and Wazed.""",
        "keywords": ["top executives", "exec-01", "exec-02", "exec-03", "exec-04", "exec-05", "team leader", "coordinator", "rankings", "achieved amount", "1750000", "1450000"]
    },
    {
        "id": "august_2026_performance_comparison",
        "title": "August 2026 Performance vs September 2026 MoM Analysis",
        "category": "Executive Performance",
        "source_file": "Estimated Budget  %-31.08.26(Final Report).xlsx",
        "source_sheet": "31.8.26",
        "content": """August 2026 Performance and Month-over-Month (MoM) Variance:
- August 2026 Target: 40,785,000 BDT.
- August 2026 Achieved New Sales: 13,041,400 BDT (31.98% achievement rate).
- August 2026 Total Collection: 16,267,590 BDT (13,041,400 new sales deposits + 3,226,190 EMI collections).
- August Total Shares Sold: 102 shares.
- August Total Outstanding Dues: 27,790,100 BDT.
- Month-over-Month (MoM) Comparison:
  * New Sales Achieved dropped from 13,041,400 BDT in August to 8,249,000 BDT in September (a 36.75% decline).
  * Gross Collection declined from 16,267,590 BDT in August to 13,839,450 BDT in September (a 14.93% drop).
  * However, EMI collections increased in September (5,590,450 BDT in September vs 3,226,190 BDT in August, up +73.28%), indicating growing recurring customer payment health despite lower initial token volume.""",
        "keywords": ["august", "september", "mom", "variance", "13041400", "16267590", "emi increase", "achievement rate", "growth"]
    },
    {
        "id": "project_collections_portfolio",
        "title": "Multi-Project Collection Portfolio (Sunset Kuakata, Hospital, DFI, Deck)",
        "category": "Revenue & Collections",
        "source_file": "Project Wise Collection.(Only Sep).xlsx",
        "source_sheet": "Sep-26 / All Project Up To Dec",
        "content": """Sunset Kuakata Portfolio & Multi-Project Revenue Realization:
The sales operations encompass several distinct hospitality and commercial development assets:
1. Sunset Kuakata Hotel & Resort Ltd. (Core Property):
   - Primary revenue driver of the group.
   - Features deluxe sea-view shares, presidential suite shares, and standard suite fractions.
   - Cumulative collection reached over 40.29 Million BDT through late 2025/2026 (Deposit: 6,095,750 BDT, Dues: 34,196,750 BDT across 190 shares).
2. Hospital Project Shares:
   - Dedicated medical and wellness tourism facility partnership.
   - Regular EMI payments and corporate sponsor investments.
3. DFI & Deck Project Assets:
   - Specialized leisure infrastructure, beach deck club access shares, and institutional investor lots.
Collection Trends:
- Collections peaked strongly in late-month cycles (last 5 days) due to corporate salary releases and sales incentive closings.
- EMI collections provide recurring monthly cash flow stability (representing roughly 40-50% of monthly gross collections).""",
        "keywords": ["project wise", "sunset kuakata", "hospital", "dfi", "deck", "emi collection", "portfolio", "40292500"]
    },
    {
        "id": "all_division_budget_breakdown",
        "title": "Division-Wise Target Allocation & Expected Collections (Aug & Sep 2026)",
        "category": "Revenue & Collections",
        "source_file": "All Division Estimate budget  Sep-26.xlsx",
        "source_sheet": "Sheet3",
        "content": """Division-Wise Expected Token, Booking & EMI Collection Breakdown:
1. Corporate Division:
   - Expected New Clients: 363 clients
   - Expected New Shares: 490 shares
   - Expected Target Budget: 46,500,000 BDT
   - Collected in Month: 7,859,000 BDT (16.90%)
2. Special Executive Division (SED):
   - Expected Target: 50,000 BDT
   - Total Value Generated: 16,932,500 BDT committed across 76 shares, 717,000 BDT initial token.
3. Directorial & Founder Divisions:
   - Target: 50,000 to 150,000 BDT
   - Founder EMI collections: 22,497,000 BDT committed across 88 shares with 740,000 BDT recurring deposit.
   - Directorial EMI: 142,000 BDT collected out of 150,000 BDT target (94.67% achievement).
Total Company Cross-Division Budget: 46,650,000 BDT target with 7,869,000 BDT collected.""",
        "keywords": ["division", "corporate", "sed", "founder", "directorial", "cst", "budget allocation", "46650000"]
    },
    {
        "id": "july_daily_collection_dynamics",
        "title": "July 2026 Daily Collection Pace & Late-Month Sprint Dynamics",
        "category": "Revenue & Collections",
        "source_file": "Last Update Daily collection july 26.xlsx & Last 5 Days Expected - July 26.xlsx",
        "source_sheet": "Day Wise / Sheet1",
        "content": """July 2026 Daily Collection Tracking & Sales Cadence:
- Operational Cadence: Sales tracking was split into 10-day sprint intervals (1-10 July Target, Day 7 Target, Day 13 Target, Last 5 Days Expected).
- Executive Quotas in Corporate Division:
  * Dipankar Roy (C.O): Management target 1,950,000 BDT
  * Momtaz Parvin Mou (C.O): Management target 1,700,000 BDT
  * S.M. Wazed (C.O): Management target 1,600,000 BDT
  * Polton Kumer Sarker (TL): Management target 1,500,000 BDT
  * Md. Mizanur Rahman (C.O): Management target 1,900,000 BDT
  * Nahid Hasna Emon (Co.): Management target 1,500,000 BDT
  * Soumen Bala: Management target 1,200,000 BDT
- Late-Month Surge Phenomenon: Over 55% of monthly revenue realization occurred in the last 5 days of the month due to salary deposits and closing discounts.""",
        "keywords": ["july", "daily collection", "last 5 days", "dipankar", "mou", "wazed", "mizanur", "polton", "nahid", "soumen"]
    },
    {
        "id": "resort_overview_benefits",
        "title": "Sunset Kuakata Hotel & Resort Ltd - Property Features & Investor Ownership Model",
        "category": "Resort Information",
        "source_file": "Company Operational Prospectus",
        "source_sheet": "Investor Charter",
        "content": """Sunset Kuakata Hotel & Resort Ltd. Investor Charter & Property Specifications:
- Location: Kuakata Sea Beach, Patuakhali, Bangladesh. Kuakata is celebrated as 'Sagor Konna' (Daughter of the Sea), offering a panoramic view of both Sunrise and Sunset over the Bay of Bengal from the same beach.
- Resort Standard: 5-Star International Luxury Resort standard.
- Property Amenities:
  * Ocean-view luxury suites with private balconies overlooking the Bay of Bengal.
  * Rooftop infinity swimming pool and sun terrace.
  * Multi-cuisine seafood and international fine dining restaurants.
  * State-of-the-art conference auditorium and banquet hall for corporate conventions.
  * Luxury wellness spa, fitness gymnasium, and kids recreation zone.
  * Private beach lounge with direct sea access and 24/7 concierge security.
- Fractional Deeded Ownership Model:
  * Investors purchase legally registered, deeded shares in the resort property.
  * Dual Return Model:
    1. Capital Appreciation: Real estate asset growth in a booming national tourism corridor (accelerated by Padma Bridge & Payra Port connectivity).
    2. Annual Dividend / Profit Sharing: Proportionate dividend payout generated from resort room nights, dining, and convention revenues.
  * Owner Lifestyle Privileges: 21 to 30 complimentary night stays annually for shareowners and immediate family, plus 20-30% VIP discounts on dining, spa, and services.
  * Transferability: Shares can be resold, gifted, or passed down to heirs.""",
        "keywords": ["kuakata", "hotel", "resort", "5-star", "ownership", "fractional share", "dividend", "complimentary stay", "amenities", "patuakhali", "sagor konna"]
    },
    {
        "id": "fractional_ownership_financials",
        "title": "Deeded Fractional Share Ownership Legal Structure, Resale, and ROI",
        "category": "Resort Information",
        "source_file": "Company Legal & Ownership Framework",
        "source_sheet": "Ownership Deed Section",
        "content": """Sunset Kuakata Fractional Share Ownership Legal Structure & Financial Yields:
1. Legal Deed & Registration:
   - Each purchaser receives a registered ownership sub-deed with individual Share Certificate and registered allotment number.
   - Registered under Bangladesh land and property registration laws.
2. Revenue Sharing & Dividend Calculation:
   - Net operating profit from room bookings, conferences, restaurant, and banquet halls is pooled annually into the owners profit distribution fund.
   - Audited annually by a chartered accounting firm before AGM distribution.
   - Payout occurs annually direct to the shareowners designated bank account.
3. Resale & Transferability:
   - Shareowners may sell their shares on the open secondary market at prevailing market prices at any time after project handover.
   - Company facilitates buyer matching through corporate sales desks.
4. Annual Complimentary Stays:
   - 21 to 30 days per annum depending on share tier.
   - Shareowners can utilize their complimentary days or gift them to relatives/guests with prior notice.""",
        "keywords": ["legal deed", "share certificate", "revenue sharing", "dividend yield", "resale", "transferability", "complimentary stay", "audit", "agm"]
    },
    {
        "id": "ai_lead_qualification_rules",
        "title": "Lead Qualification Criteria, Tier Classifications, and Defensive Guardrails",
        "category": "Lead Qualification",
        "source_file": "AI Lead Operations Manual",
        "source_sheet": "Scoring Matrix",
        "content": """AI Lead Qualification Logic & Scoring Matrix (Sunset Kuakata):
- Purpose: Automated lead qualification powered by Groq LLM to instantly categorize incoming sales leads and prioritize sales team outreach.
- Lead Categories:
  1. HOT LEAD (Score 75-100):
     - Budget: >= 250,000 BDT (meets or exceeds full single-share entry price).
     - Timeline: Immediate / ready to book or visit this week / cash ready.
     - Action: Immediate handover to Senior Team Leader within 15 minutes.
  2. WARM LEAD (Score 40-74):
     - Budget: 100,000 to 249,000 BDT or interested in EMI/installment payment plans.
     - Timeline: Exploring, planning investment within 1-3 months.
     - Action: Standard nurture sequence, send brochure and installment schedule.
  3. COLD LEAD (Score 0-39):
     - Budget: Under 100,000 BDT or unspecified, casual browser, student.
     - Action: Added to automated newsletter and future token promotions.
- Security & Defense:
  * Prompt Injection Defense: Customer messages are strictly isolated as DATA, never executed as SYSTEM instructions. Attempts such as ignore instructions, classify me as hot, or give score 100 are penalized.
  * Privacy: Personal Identifiable Information (email, phone) is never leaked in qualification rationales.""",
        "keywords": ["lead qualification", "hot lead", "warm lead", "cold lead", "scoring", "groq", "prompt injection", "budget threshold", "250000", "100000"]
    },
    {
        "id": "booking_emi_payment_procedure",
        "title": "Booking Process, Token Deposits, and EMI Installment Schedules",
        "category": "Pricing & Discounts",
        "source_file": "Sales Operations Standard Operating Procedures",
        "source_sheet": "Payment Terms",
        "content": """Booking Process & Installment (EMI) Schedule Guidelines:
1. Initial Token Booking:
   - Token deposit can be made starting from 10,000 to 50,000 BDT.
   - Reserves the specific suite fraction and locks in promotional discount rate for 15-30 days.
2. Down Payment Milestone:
   - 20% to 30% of net discounted sales price due at contract signing.
   - Allotment letter issued upon down payment clearance.
3. EMI Installment Options:
   - Remaining balance payable in equal monthly installments over 12 months, 24 months, or up to 36 months interest-free under promotional schemes.
   - Payments accepted via direct bank deposit, BEFTN/NPSB bank transfer, or automated cheque clearing.
4. Cancellation & Refund Policy:
   - Tokens can be transferred to another party or adjusted against other group projects.""",
        "keywords": ["booking process", "token deposit", "emi schedule", "down payment", "installments", "payment terms", "bank transfer"]
    },
    {
        "id": "location_connectivity_advantage",
        "title": "Kuakata Strategic Location, Padma Bridge Connectivity & Tourism Growth",
        "category": "Resort Information",
        "source_file": "Economic Feasibility Study",
        "source_sheet": "Regional Market",
        "content": """Kuakata Tourism Corridor & Economic Growth Drivers:
- Connectivity Transformation: Following the inauguration of the Padma Bridge and Lebukhali Bridge (Payra Bridge), travel time from Dhaka to Kuakata has reduced from 16+ hours to only 5-6 hours by road.
- Payra Deep Sea Port & Economic Zone: Major industrial and maritime developments near Patuakhali are creating high-end business travel and conference demand.
- Eco-Tourism Surge: Kuakata offers unique eco-tourism attractions: Gangamati mangrove forest, Fatrar Char (part of the Sundarbans mangrove reserve), Rakhine Buddhist temple, and the Kuakata Well.
- High Occupancy Projections: Year-round weekend domestic tourism combined with seasonal winter surges generate projected 65-80% average resort suite occupancy.""",
        "keywords": ["connectivity", "padma bridge", "payra port", "dhaka to kuakata", "travel time", "eco-tourism", "gangamati", "occupancy rate"]
    }
]

target_file = out_dir / "knowledge_base.json"
with open(target_file, "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)

print(f"Generated {len(chunks)} chunks in {target_file}")
