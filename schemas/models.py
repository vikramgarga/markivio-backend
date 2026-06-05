from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


# ── Intake dropdown options ────────────────────────────────────────────────────

INDUSTRY_OPTIONS: list[str] = [
    "FMCG / Consumer Goods",
    "Food & Beverage",
    "Fashion & Apparel",
    "Beauty & Personal Care",
    "Healthcare & Pharma",
    "Retail & E-commerce",
    "Technology & SaaS",
    "Financial Services & Fintech",
    "Education & EdTech",
    "Real Estate & Construction",
    "Automotive",
    "Travel & Hospitality",
    "Media & Entertainment",
    "Agriculture & AgrTech",
    "Manufacturing & Industrial",
    "Non-Profit & Social Impact",
    "Professional Services",
    "Other",
]

CHALLENGE_OPTIONS: list[str] = [
    "Low brand awareness",
    "Poor customer retention / high churn",
    "Unclear brand positioning",
    "Ineffective digital presence",
    "Weak lead generation",
    "High customer acquisition cost",
    "Entering a new market or geography",
    "Launching a new product or category",
    "Competing against a dominant incumbent",
    "Rebranding or repositioning",
    "Inconsistent brand experience across channels",
    "Building a B2B sales pipeline",
    "Growing in a price-sensitive market",
    "Limited marketing budget",
    "Team lacks marketing capability",
    "Other",
]

INSPIRATION_BRAND_OPTIONS: list[str] = [
    # ── Consumer Technology & Hardware ────────────────────────────────────────
    "Apple [Consumer Tech] — simplicity, premium design, end-to-end ecosystem lock-in",
    "Dyson [Consumer Tech] — engineering-as-brand, reinventing mundane household categories",
    "Samsung [Consumer Tech] — mass-premium positioning, global scale with local relevance",
    "Sony [Consumer Tech] — heritage + reinvention, PlayStation community, entertainment ecosystem",
    "Sonos [Consumer Tech] — premium audio, seamless multi-room UX, home ecosystem",
    "GoPro [Consumer Tech] — community-generated content as primary marketing, lifestyle identity",
    "Nest/Google Home [Consumer Tech] — smart home, design-led hardware in a commoditised space",
    "Bose [Consumer Tech] — sound science as brand story, premium noise-cancellation category creator",
    "Logitech [Consumer Tech] — quiet B2B2C dominance, accessories as category, WFH pivot",
    "Xiaomi [Consumer Tech] — ecosystem of 200+ products, community-first, internet-as-channel",
    "OnePlus [Consumer Tech] — 'Never Settle' community cult, flagship killer positioning",
    "NVIDIA [Semiconductors] — from gaming GPU to AI infrastructure, platform ecosystem brand",
    "TSMC [Semiconductors B2B] — pure-play trust, strategic partner to the world's chip designers",
    "ARM [Semiconductors B2B] — licensing model, hidden architecture inside every smartphone",
    # ── B2B Software & SaaS ───────────────────────────────────────────────────
    "Salesforce [B2B SaaS] — category creation (CRM), Ohana culture, ecosystem of partners",
    "HubSpot [B2B SaaS] — inbound marketing as a category invented by the brand itself",
    "Slack [B2B SaaS] — bottom-up viral adoption, personality-led brand in an enterprise world",
    "Notion [B2B SaaS] — community evangelism, flexibility as the product's core promise",
    "Figma [B2B SaaS] — real-time collaboration as category creation, community & templates",
    "Canva [B2B/B2C SaaS] — democratising design, freemium to team plans, global-local templates",
    "Stripe [B2B SaaS] — developer-first GTM, documentation as marketing, API-first brand",
    "Shopify [B2B/B2C] — empowering the underdog merchant, platform + ecosystem play",
    "Atlassian [B2B SaaS] — PLG at enterprise scale, self-serve, low-touch expansion",
    "Snowflake [B2B SaaS] — data cloud category creation, consumption-based pricing as brand signal",
    "Twilio [B2B SaaS] — developer trust, CPaaS category creation, 'Ask your developer'",
    "ServiceNow [B2B SaaS] — workflow automation for enterprises, making work flow as tagline",
    "Workday [B2B SaaS] — cloud-first HR & Finance, trust in a data-sensitive category",
    "Zoom [B2B SaaS] — ease-of-use as moat, category that became a verb during COVID",
    "Monday.com [B2B SaaS] — work OS positioning, visual-first, SMB to enterprise motion",
    "Zoho [B2B SaaS, India] — integrated 50-product suite, bootstrapped, frugal innovation",
    "Freshworks [B2B SaaS, India] — David vs Goliath positioning, India-built for global SMBs",
    "Postman [B2B SaaS, India-origin] — API platform, developer community as growth engine",
    # ── E-commerce, Marketplace & Retail ─────────────────────────────────────
    "Amazon [E-commerce] — customer obsession, flywheel model, logistics as competitive moat",
    "Alibaba [E-commerce] — ecosystem of commerce, payments, cloud, and entertainment",
    "Shopify [Retail Platform] — powering the independent merchant, anti-Amazon positioning",
    "Warby Parker [DTC Retail] — affordable premium, buy-one-give-one social mission",
    "Chewy [E-commerce] — emotional customer service, pet parent identity, handwritten cards",
    "Zappos [E-commerce] — WOW service culture, returning shoes as brand expression",
    "Etsy [Marketplace] — artisan community, authentic human-to-human commerce",
    "IKEA [Retail] — democratising design, flat-pack storytelling, showroom as experience",
    "Costco [Retail] — membership model, treasure hunt retail, employee-first culture",
    "Zara/Inditex [Fashion Retail] — data-driven fast fashion, vertical integration, zero advertising",
    "Nykaa [E-commerce, India] — beauty category creation, content-to-commerce, omni-channel",
    "Meesho [Social Commerce, India] — Tier 2/3 India, reseller empowerment, WhatsApp commerce",
    "Flipkart [E-commerce, India] — market creation, logistics infrastructure, Big Billion Days",
    "Reliance Retail [Retail, India] — physical + digital convergence, JioMart ecosystem",
    # ── FMCG & Consumer Goods ─────────────────────────────────────────────────
    "P&G [FMCG] — purpose-led brands at scale, house of brands vs. branded house strategy",
    "Unilever [FMCG] — Sustainable Living Plan, proving purpose and profit coexist at scale",
    "Nestlé [FMCG] — nutrition repositioning of legacy portfolio, trust through 150 years",
    "Reckitt [FMCG] — power brands in health & hygiene, Dettol trust through COVID",
    "Colgate-Palmolive [FMCG] — category ownership (toothpaste), expansion into adjacent needs",
    "Oatly [FMCG] — radical honesty, anti-corporate tone, packaging as media",
    "Impossible Foods [FMCG] — science-led storytelling, disrupting a 10,000-year-old category",
    "Beyond Meat [FMCG] — B2B restaurant channel to build B2C awareness and credibility",
    "Tony's Chocolonely [FMCG] — mission-first brand, supply chain justice as product story",
    "Amul [FMCG, India] — cooperative model, topical advertising, mass-market wit for 70 years",
    "Dabur [FMCG, India] — Ayurveda modernised for urban India, rural-urban bridge portfolio",
    "Marico [FMCG, India] — premiumisation of commodity categories, portfolio diversification",
    "Godrej Consumer [FMCG, India] — Africa + Asia emerging market expansion, Goodknight trust",
    "Fevicol/Pidilite [FMCG, India] — product-as-hero advertising, B2B2C adhesive category",
    "ITC [FMCG, India] — diversified conglomerate pivoting to FMCG at scale, e-Choupal rural model",
    "Hindustan Unilever [FMCG, India] — rural distribution mastery, Project Shakti, premiumisation",
    # ── Food & Beverage ───────────────────────────────────────────────────────
    "Starbucks [F&B] — third place concept, personalisation ritual, loyalty programme mastery",
    "McDonald's [F&B] — consistency at global scale, franchisee model, local menu adaptation",
    "Chipotle [F&B] — transparent supply chain as brand, 'Food with Integrity'",
    "Blue Bottle Coffee [F&B] — craft-as-luxury, anti-chain positioning, acquired by Nestlé",
    "Sweetgreen [F&B] — digital-first salad chain, local sourcing, tech-led unit economics",
    "Red Bull [F&B] — content and events ARE the product; media company that sells energy drinks",
    "Diageo [F&B] — portfolio of premium spirits, occasion-based brand architecture",
    "Anheuser-Busch InBev [F&B] — premiumisation strategy, global brands + local heroes",
    "Danone [F&B] — mission-led dairy & water, B Corp at scale, 'One Planet. One Health'",
    "Paper Boat [F&B, India] — nostalgia marketing, packaging-as-storytelling, indigenous flavours",
    "Chai Point [F&B, India] — organised chai, scalable desi experience, B2B workplace channel",
    "Maaza/Coca-Cola India [F&B, India] — localising a global brand, mango as emotional territory",
    # ── Fashion, Apparel & Sportswear ─────────────────────────────────────────
    "Nike [Sportswear] — emotional storytelling, athlete identity, Just Do It as a philosophy",
    "Adidas [Sportswear] — culture + sport collaboration, Yeezy model, creator partnerships",
    "Patagonia [Outdoor] — radical purpose, 'Don't Buy This Jacket', anti-consumerism as brand",
    "Lululemon [Apparel] — community-first brand, ambassador model, premium athleisure category",
    "Supreme [Streetwear] — artificial scarcity, drop culture, community gatekeeping as strategy",
    "H&M [Fast Fashion] — conscious collection alongside fast fashion, sustainability tension",
    "Burberry [Luxury Fashion] — heritage brand digital reinvention, Snapchat-first luxury launch",
    "Hermès [Luxury] — scarcity by design, craft narrative, waiting list as brand mechanism",
    "boAt [Audio/Fashion, India] — aspirational youth, affordable cool, D2C + marketplace hybrid",
    "Fabindia [Apparel, India] — Indian craft at scale, artisan livelihood as brand story",
    # ── Beauty & Personal Care ────────────────────────────────────────────────
    "Dove [Beauty] — real beauty platform, 20-year consistent purpose, social experiment ads",
    "Glossier [Beauty] — community-built brand, Instagram-native, VC of customer voice",
    "Fenty Beauty [Beauty] — radical inclusivity (40 shades) as product strategy, not just message",
    "The Ordinary/DECIEM [Beauty] — ingredient transparency, anti-marketing marketing, cult trust",
    "Charlotte Tilbury [Beauty] — founder-as-brand, glamour democratised, experiential retail",
    "Mamaearth [Beauty, India] — D2C trust-building, toxin-free positioning, digital-first",
    "Bombay Shaving Company [Beauty, India] — male grooming storytelling, DTC to retail",
    "Sugar Cosmetics [Beauty, India] — bold women, long-lasting formula, offline expansion story",
    "Plum [Beauty, India] — vegan + cruelty-free positioning, ingredient-conscious millennials",
    # ── Automotive & Mobility ─────────────────────────────────────────────────
    "Tesla [Auto] — software-first vehicle, OTA updates, zero paid advertising, cult community",
    "Toyota [Auto] — Kaizen & TPS, quality & reliability promise, Lexus as premium brand strategy",
    "BYD [Auto] — vertical integration of battery + EV, mass-market EV at China scale",
    "BMW [Auto] — 'The Ultimate Driving Machine', engineering heritage, premium defensible",
    "Rivian [Auto] — adventure-first EV, Amazon partnership as B2B anchor, DTC retail",
    "Maruti Suzuki [Auto, India] — trust for 40 years, after-sales network as moat, India-first design",
    "Ola Electric [Auto, India] — DTC EV disruption, manufacturing at scale, young India brand",
    "Uber [Mobility] — category creation, surge pricing as controversy, global-local adaptation",
    "Rapido [Mobility, India] — bike taxi for Bharat, hyper-local, gig economy brand",
    # ── Industrial, Manufacturing & Engineering ───────────────────────────────
    "3M [Industrial] — 15% innovation time, 60,000-product portfolio, scientist-as-hero culture",
    "Siemens [Industrial B2B] — digital twin leadership, industrial metaverse, engineering trust",
    "Caterpillar [Industrial B2B] — iron brand, global dealer network as distribution moat",
    "Bosch [Industrial B2B] — 'Invented for Life', quality across 14 divisions, IoT pivot",
    "GE [Industrial B2B] — industrial internet brand (Predix), pivot from conglomerate to focused",
    "Honeywell [Industrial B2B] — industrial IoT, safety-as-brand in hazardous industries",
    "ABB [Industrial B2B] — robotics & automation leadership, electrification for net zero",
    "Schneider Electric [Industrial B2B] — energy management, sustainability as B2B brand story",
    "L&T [Engineering, India] — nation-builder brand, infrastructure at civilizational scale",
    "Tata Steel [Industrial, India] — decarbonisation commitment, 'Values Stronger Than Steel'",
    # ── Aerospace, Defence & Space ────────────────────────────────────────────
    "SpaceX [Aerospace] — moonshot ambition as brand, reusable rocket = cost disruption",
    "Airbus [Aerospace B2B] — European engineering pride, A380 ambition vs. 787 market read",
    "Boeing [Aerospace B2B] — safety trust recovery, brand after crisis case study",
    "ISRO [Space, India] — frugal innovation, national pride, Mangalyaan at Mars rover cost",
    # ── Energy, Utilities & Sustainability ───────────────────────────────────
    "Ørsted [Energy] — fossil fuel company fully transformed to offshore wind, purpose pivot",
    "Tesla Energy [CleanTech] — Powerwall + grid storage, energy brand extension from auto",
    "NextEra Energy [Energy B2B] — largest renewable energy utility, investor confidence in green",
    "Adani Green [Energy, India] — scale of renewables ambition, controversial conglomerate brand",
    "ReNew Power [CleanTech, India] — India's clean energy champion, ESG narrative for investors",
    # ── Agriculture, Food Systems & AgriTech ─────────────────────────────────
    "John Deere [AgriTech] — precision farming, connected equipment, 'Nothing Runs Like a Deere'",
    "Corteva [AgriTech] — science-led seed + crop protection, farmer as customer, data platform",
    "DeHaat [AgriTech, India] — full-stack farmer platform, input + advisory + output linkage",
    "Ninjacart [AgriTech, India] — farm-to-retail supply chain, cold chain infrastructure brand",
    "NDDB/Amul [AgriTech, India] — cooperative model, Operation Flood, farmer ownership brand",
    # ── Healthcare, Pharma & Life Sciences ───────────────────────────────────
    "Johnson & Johnson [Healthcare] — Credo-led trust, multi-category Tylenol crisis recovery",
    "Philips [Healthcare] — consumer electronics to health tech pivot, meaningful innovation",
    "Medtronic [MedTech B2B] — patient outcomes as the only brand KPI, 'Mission of Medtronic'",
    "Novo Nordisk [Pharma] — Ozempic obesity category redefinition, disease area ownership",
    "Pfizer [Pharma] — COVID mRNA speed-to-market, science communication brand",
    "Apollo Hospitals [Healthcare, India] — quality + scale + medical tourism, trust at scale",
    "Narayana Health [Healthcare, India] — cardiac care at ₹1 lakh, frugal innovation in health",
    "Lemonade [Insurtech] — AI-first insurance, radical transparency, giveback model",
    "Oscar Health [Insurtech] — human-centred health insurance, concierge for Millennials",
    # ── Financial Services, Fintech & Banking ─────────────────────────────────
    "Visa [Payments] — B2B2C network effect, invisible infrastructure, priceless campaign",
    "Mastercard [Payments] — sensory branding (sound logo), dropping name from logo, purpose",
    "American Express [Financial] — premium membership, small business advocacy, closed loop",
    "Stripe [Fintech B2B] — developer trust, API docs as brand, internet GDP as frame",
    "Square/Block [Fintech] — democratising payments for small merchants, Cash App ecosystem",
    "Chime [Neobank] — no-fee banking, underbanked empathy, financial health as mission",
    "Revolut [Neobank] — hyper-feature velocity, global travel card, borderless money brand",
    "Zerodha [Fintech, India] — zero brokerage disruption, investor education, community-led",
    "Groww [Fintech, India] — simplifying investing for first-time investors, Millennials trust",
    "PhonePe [Fintech, India] — UPI scale, merchant payments, insurance & mutual fund extension",
    "HDFC Bank [Banking, India] — consistent service quality, trusted premium, network depth",
    "Bajaj Finance [NBFC, India] — lending at consumer electronics point-of-sale, EMI culture",
    # ── Travel, Hospitality & Logistics ──────────────────────────────────────
    "Airbnb [Travel] — community, belonging, trust-first peer marketplace, experience economy",
    "Marriott/Ritz-Carlton [Hospitality] — employee-first service culture, gold standards brand",
    "Oyo [Hospitality, India] — asset-light hotel aggregation, budget standardisation, scale",
    "MakeMyTrip [Travel, India] — online travel category creation, TV-first D2C, bundling",
    "Maersk [Logistics B2B] — supply chain trust, digital transformation of ocean shipping",
    "DHL [Logistics B2B] — yellow brand consistency, reliability promise at global scale",
    "Flexport [Logistics B2B] — software-first freight forwarding, data visibility as moat",
    "IndiGo [Aviation, India] — on-time performance as brand, low-cost operational excellence",
    "Delhivery [Logistics, India] — tech-first last-mile, B2B D2C backbone, IPO brand story",
    # ── Telecommunications & Infrastructure ───────────────────────────────────
    "Jio [Telecom, India] — free data disruption, 400M subscriber base, ecosystem lock-in",
    "T-Mobile USA [Telecom] — 'Un-carrier' anti-establishment positioning, contract destruction",
    "Vodafone [Telecom] — 'Power to You', global-local brand consistency, ZooZoo India campaign",
    "Airtel [Telecom, India] — premium network positioning, 'Har Ek Friend Zaroori Hota Hai'",
    # ── Media, Entertainment, Gaming & Sports ─────────────────────────────────
    "Netflix [Media] — personalisation engine, content as strategy, global-local originals",
    "Disney [Media] — IP universe, franchise monetisation, multi-generational emotional equity",
    "Spotify [Media] — data storytelling (Wrapped), playlist as identity, podcast pivot",
    "YouTube [Media] — creator economy platform, democratising video, algorithm-as-brand",
    "Nintendo [Gaming] — joy as brand philosophy, IP longevity, blue ocean hardware strategy",
    "Epic Games/Fortnite [Gaming] — live service model, cultural crossovers, metaverse ambition",
    "Riot Games [Gaming] — community obsession, Esports brand, Valorant launch as content event",
    "Manchester City/CFG [Sports] — data analytics, global city network, sportswashing debate",
    "Red Bull Racing [Sports] — brand as team, sport as marketing, content franchise",
    "Dream11 [Sports, India] — fantasy sports category creation, cricket fandom monetisation",
    # ── Education & Human Capital ─────────────────────────────────────────────
    "Duolingo [EdTech] — gamification, unhinged social media persona, habit loop design",
    "Khan Academy [EdTech] — free world-class education, mission as the entire brand",
    "Coursera [EdTech] — university partnerships, credentials for lifelong learners",
    "Byju's [EdTech, India] — aggressive growth, celebrity endorsement, aspirational parent brand",
    "Unacademy [EdTech, India] — educator-as-creator, live learning, competitive exam focus",
    "Vedantu [EdTech, India] — live tutoring, WAVE platform, trust through teacher quality",
    # ── Luxury & Premium Goods ────────────────────────────────────────────────
    "Hermès [Luxury] — scarcity by design, craft as religion, Birkin as cultural artifact",
    "LVMH [Luxury] — house of 75 brands, savoir-faire, controlled distribution as strategy",
    "Rolex [Luxury] — time as investment, aspiration engineered over 120 years",
    "Tiffany & Co. [Luxury] — blue box as experience, accessible luxury gateway strategy",
    "Tanishq/Titan [Jewellery, India] — organised jewellery trust, emotional advertising, karatometer",
    # ── Professional Services & Consulting ────────────────────────────────────
    "McKinsey & Company [Professional Services] — knowledge brand, thought leadership as GTM",
    "Deloitte [Professional Services] — purpose at scale, 'For what matters', integrated services",
    "WPP [Professional Services] — creative holding company, agency network as portfolio brand",
    # ── Non-Profit, Social Enterprise & Development ───────────────────────────
    "Grameen Bank [Social Finance] — microcredit model, banking the unbanked, Nobel-winning brand",
    "BRAC [Development] — largest NGO in the world, integrated rural development model",
    "Gates Foundation [Philanthropy] — strategic philanthropy, metrics-driven giving, global health",
    "Teach For India [Education] — fellowship model, urban-rural education bridge, alumni network",
    "GiveDirectly [Philanthropy] — radical simplicity, direct cash transfers, evidence-based giving",
    "Selco [Social Enterprise, India] — solar energy for rural poor, proof that profitability and impact coexist",
    # ── India Conglomerates & National Champions ───────────────────────────────
    "Tata Group [Conglomerate, India] — 150-year trust, nation-building narrative, salt to software",
    "Mahindra Group [Conglomerate, India] — Rise philosophy, SUV brand, rural + urban bridge",
    "Bajaj Group [Conglomerate, India] — scooter to motorcycle to finance, brand reinvention story",
    "Wipro [IT Services, India] — sustainability leadership in IT, Azim Premji philanthropy brand",
    "Infosys [IT Services, India] — education-led employer brand, Mysore campus as culture signal",
    "Other — I'll describe it",
]

INNOVATION_TECHNIQUE_OPTIONS: list[str] = [
    # ── Design Thinking & Human-Centred Design ────────────────────────────────
    "Design Thinking (Stanford d.school) — Empathise → Define → Ideate → Prototype → Test",
    "Double Diamond (UK Design Council) — Discover & Define (problem), Develop & Deliver (solution)",
    "Human-Centred Design (IDEO) — deep user empathy drives every design decision",
    "Triple Diamond — extended HCD adding a third diamond for implementation & learning",
    "Service Design — designing the full end-to-end service, front stage and back stage",
    "Service Blueprint — map actors, actions, and systems across visible and invisible layers",
    "Participatory Design / Co-design — users as active co-creators, not just research subjects",
    "Experience Prototyping — simulate service or product in context before building",
    "Speculative Design — design fictional futures to provoke strategic conversation",
    "Transition Design — designing for systemic, long-term societal change",
    # ── Discovery, Research & Customer Insight ────────────────────────────────
    "Jobs-to-be-Done / JTBD (Christensen) — what progress is the customer trying to make?",
    "Outcome-Driven Innovation / ODI (Ulwick) — quantify unmet customer outcomes, not just jobs",
    "Empathy Mapping — what users say, think, do, and feel; surface gaps",
    "Customer Journey Mapping — end-to-end touchpoint, emotion, and pain analysis",
    "Experience Mapping — broader than CJM; maps life context, not just product interaction",
    "Mental Model Mapping (Indi Young) — align offering to how users actually think",
    "Ethnographic Research / Contextual Inquiry — observe users in their natural environment",
    "Diary / Experience Sampling Studies — capture in-the-moment behaviour over time",
    "Voice of Customer (VoC) + Quality Function Deployment (QFD) — translate customer needs to specs",
    "Kano Model — classify features: Basic, Performance, and Delight drivers",
    "Conjoint Analysis — statistically measure how customers make trade-off decisions",
    "MaxDiff Analysis — identify the most and least important features from a large set",
    "Net Promoter System (NPS) — loyalty measure, inner loop learning, closed-loop feedback",
    "5 Whys (Sakichi Toyoda) — iterative root cause analysis",
    "Fishbone / Ishikawa Diagram — cause-and-effect mapping for complex problems",
    "How Might We (HMW) Questions — reframe problem statements as open opportunity questions",
    "Assumption Mapping — surface, test, and prioritise hidden project assumptions",
    "Pre-Mortem Analysis — imagine the project failed; work backwards to prevent it",
    "Consumer Decision Journey (McKinsey) — loyalty loop, initial consideration, active evaluation",
    "Zero Moment of Truth / ZMOT (Google) — the research moment before the first moment of truth",
    # ── Strategy & Competitive Analysis ──────────────────────────────────────
    "Blue Ocean Strategy (Kim & Mauborgne) — create uncontested market space via ERRC grid",
    "Disruptive Innovation (Christensen) — target over-served or non-consumers to displace leaders",
    "Sustaining vs. Disruptive Innovation — diagnostic framework for where to compete",
    "Crossing the Chasm (Geoffrey Moore) — bridge the gap from early adopters to early majority",
    "Technology Adoption Lifecycle (Rogers) — Innovators → Early Adopters → Early/Late Majority → Laggards",
    "Diffusion of Innovations — plan for adoption curve; design for each adopter segment",
    "Ansoff Growth Matrix — penetration, market development, product development, diversification",
    "Porter's Five Forces — rivalry, new entrants, substitutes, buyer power, supplier power",
    "Porter's Generic Strategies — cost leadership, differentiation, or focus",
    "Porter's Value Chain — primary and support activities where margin is created and captured",
    "Porter's Diamond Model — national competitive advantage; for market entry decisions",
    "BCG Growth-Share Matrix — Stars, Cash Cows, Question Marks, Dogs; portfolio resource allocation",
    "BCG Advantage Matrix — fragmented, volume, specialised, stalemate; where to compete",
    "GE-McKinsey Matrix — 9-box portfolio assessment on market attractiveness vs. business strength",
    "McKinsey 3 Horizons — H1 core, H2 adjacency, H3 new ventures; simultaneous investment logic",
    "McKinsey Strategic Staircase — Profit from the Core (Zook), adjacency expansion logic",
    "Wardley Mapping — value chain evolution map; situational awareness for strategy",
    "Platform & Ecosystem Strategy — multi-sided markets, network effects, governance design",
    "Value Net (Brandenburger & Nalebuff) — Co-opetition; map complementors alongside competitors",
    "Resource-Based View (Barney) — VRIN: Valuable, Rare, Inimitable, Non-substitutable resources",
    "Dynamic Capabilities (Teece) — sense, seize, reconfigure; compete in rapidly changing markets",
    "Core Competency Framework (Prahalad & Hamel) — identify and leverage unique organisational skills",
    "Competitive War Gaming — simulate competitor responses before launching strategy",
    "Scenario Planning (Shell method) — develop 2-4 plausible futures; test strategy robustness",
    "First Principles Thinking (Aristotle/Musk) — decompose to fundamentals; rebuild from scratch",
    "Inversion (Charlie Munger) — avoid failure rather than pursue success; think backwards",
    "SWOT Analysis — strengths, weaknesses, opportunities, threats; classic situation audit",
    "TOWS Matrix — convert SWOT into strategic options (SO, ST, WO, WT)",
    "PESTLE Analysis — Political, Economic, Social, Technology, Legal, Environmental",
    "STEEP / STEEPLE — extended PESTLE adding Ethical and Ecological dimensions",
    # ── Brand Strategy & Positioning ─────────────────────────────────────────
    "STP — Segmentation, Targeting, Positioning; the spine of marketing strategy",
    "Brand Archetypes (Carl Jung / Mark & Pearson) — 12 universal characters; align brand personality",
    "Golden Circle (Simon Sinek) — Why → How → What; purpose-first communication",
    "Brand Resonance Model / CBBE (Kevin Lane Keller) — identity, meaning, response, resonance",
    "Brand Pyramid — essence at the top; values, personality, benefits, attributes below",
    "Brand Key (Unilever) — root strength, competitive environment, target, insight, benefits, reason to believe",
    "Brand Asset Valuator (BAV) — differentiation, relevance, esteem, knowledge; four pillars of brand health",
    "Perceptual Mapping — plot brand vs. competitors on two key consumer perception axes",
    "Distinctive Assets (Ehrenberg-Bass) — build memory structures, not just differentiation",
    "Mental Availability (Byron Sharp) — how easily a brand comes to mind in buying situations",
    "Physical Availability (Byron Sharp) — how easy it is for buyers to find and buy the brand",
    "Category Entry Points (CEPs) — identify and own the cues that trigger category purchase",
    "Penetration vs. Loyalty Strategy — Sharp: penetration nearly always drives growth more than loyalty",
    "Double Jeopardy Law — smaller brands have fewer buyers AND lower loyalty; predictive model",
    "Lovemark Framework (Kevin Roberts) — high love + high respect = irreplaceable brand",
    "FCB Grid — involvement (high/low) × response (think/feel); media and messaging implications",
    "Long & Short of It (Binet & Field) — balance brand building (60%) with activation (40%)",
    "4Ps / 7Ps Marketing Mix — Product, Price, Place, Promotion (+ People, Process, Physical Evidence)",
    "Brand Portfolio Strategy — house of brands vs. branded house vs. hybrid architecture",
    "Positioning Statement Framework — for [target], [brand] is the [category] that [benefit] because [RTB]",
    "Jobs-Based Segmentation — segment by the job to be done, not demographics or psychographics",
    # ── Ideation, Creative Problem-Solving & Innovation ───────────────────────
    "SCAMPER — Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse",
    "Six Thinking Hats (Edward de Bono) — parallel thinking in six structured perspectives",
    "Lateral Thinking (Edward de Bono) — indirect, non-linear approaches to break fixed thinking",
    "PO (Provocative Operation, de Bono) — deliberate provocations to generate new ideas",
    "Reverse / Negative Brainstorming — how would we guarantee failure? Then invert solutions",
    "Crazy 8s (Google Ventures Design Sprint) — 8 rough ideas in 8 minutes; force divergence",
    "Brainwriting 6-3-5 — 6 people, 3 ideas, 5 rounds; silent ideation at scale",
    "TRIZ (Altshuller) — 40 inventive principles derived from 400,000 patents; contradiction resolution",
    "ARIZ (Advanced TRIZ) — algorithm for resolving complex inventive contradictions",
    "Morphological Analysis — systematically map all variables and explore combinations",
    "Analogical Thinking / SYNECTICS — use biological, symbolic, or direct analogies to spark ideas",
    "Biomimicry (Janine Benyus) — nature's 3.8 billion years of R&D as design inspiration",
    "Cross-Industry Innovation — transplant proven solutions from an unrelated industry",
    "Frugal Innovation / Jugaad (Radjou) — do more with less; Indian reverse innovation mindset",
    "Reverse Innovation (Govindarajan) — innovations for emerging markets adopted by developed ones",
    "Open Innovation (Chesbrough) — external ideas and paths alongside internal R&D",
    "Lead User Innovation (von Hippel) — identify extreme users who face future needs today",
    "Crowdsourcing & Innovation Tournaments — structured challenges to source external ideas",
    "Random Word / Random Image Stimulus — force unrelated associations to break fixedness",
    "Mind Mapping (Tony Buzan) — radiate ideas from a central concept; visual thinking tool",
    "Assumption Storming — list all assumptions, then ask 'What if the opposite were true?'",
    "The 5 Whys — drill to root cause through iterative 'why' questioning",
    "Problem Reframing — redefine the problem statement; often the real innovation is in the question",
    # ── Lean, Agile & Product Development ────────────────────────────────────
    "Lean Startup (Eric Ries) — Build → Measure → Learn; validated learning as the unit of progress",
    "Design Sprint (Jake Knapp / Google Ventures) — 5-day structured sprint from problem to tested prototype",
    "Continuous Discovery (Teresa Torres) — weekly touchpoints with customers; opportunity solution tree",
    "Dual-Track Agile — parallel discovery and delivery tracks; prevent building the wrong thing fast",
    "MVP (Minimum Viable Product) — fastest path to learning from real users in market",
    "MLP (Minimum Lovable Product) — minimum that users actually love, not just tolerate",
    "MMP (Minimum Marketable Product) — smallest release with commercial and customer value",
    "Concierge MVP — manually deliver the service before automating; learn before you build",
    "Wizard of Oz MVP — fake the technology while humans run it behind the scenes",
    "Shape Up (Basecamp/DHH) — 6-week appetite-fixed cycles; bet, build, cool-down",
    "Agile / Scrum / Kanban — iterative delivery, sprint ceremonies, backlog prioritisation",
    "SAFe / LeSS — scaling agile across large organisations and multiple teams",
    "Rapid Prototyping — lo-fi paper, wireframe, or functional prototypes to test early",
    "Pretotype (Alberto Savoia) — test the right 'it' before building the thing right",
    "Stage-Gate Process (Robert Cooper) — structured funnel for innovation projects: idea to launch",
    "Technology Readiness Levels (TRL) — NASA-origin scale from basic research to deployment",
    "North Star Metric Framework — single metric that captures product value delivery",
    "OKRs (Doerr / Google) — Objectives and Key Results; ambitious goals with measurable outcomes",
    "HEART Framework (Google) — Happiness, Engagement, Adoption, Retention, Task Success",
    # ── Growth, Marketing & Go-to-Market ──────────────────────────────────────
    "Pirate Metrics / AARRR (Dave McClure) — Acquisition, Activation, Retention, Referral, Revenue",
    "RARRA (Reforge) — Retention, Activation, Referral, Revenue, Acquisition; retention-first lens",
    "Flywheel Model (Amazon/Collins) — compound growth loops that self-reinforce over time",
    "Product-Led Growth (PLG) — product is the primary acquisition, conversion, and expansion channel",
    "Community-Led Growth — engaged user community as distribution, retention, and NPS engine",
    "Partner-Led Growth — channel partnerships, ISVs, and resellers as growth multiplier",
    "Sales-Led / Enterprise GTM — outbound, SDR/AE motion, ABM for high-ACV deals",
    "Account-Based Marketing (ABM) — treat high-value accounts as markets of one",
    "Hook Model (Nir Eyal) — Trigger → Action → Variable Reward → Investment; habit formation",
    "Viral Loops & K-Factor — design product mechanics that make users invite others",
    "Network Effects Framework (NFX) — 13 types of network effects; defensibility mapping",
    "Bass Diffusion Model — mathematically forecast adoption curve for new products",
    "ICE Scoring — Impact, Confidence, Ease; fast experiment prioritisation",
    "RICE Scoring — Reach, Impact, Confidence, Effort; more rigorous prioritisation",
    "Bullseye Framework (Traction) — 19 channels, test all, focus on the 1-3 that work",
    "Growth Hacking — rapid experimentation across funnel stages; data-driven channel discovery",
    "T-Shaped Marketing — broad channel knowledge + deep expertise in 1-2 highest-leverage channels",
    "Full-Funnel Attribution — connect awareness investment to revenue outcomes across channels",
    "Demand Generation vs. Demand Capture — build future demand vs. capture existing intent",
    "Ehrenberg-Bass Category Buying — reach all buyers in a category lightly, not loyalists deeply",
    "Go-to-Market Fit Framework — ICP, channel, message, motion; before scaling GTM",
    "Pragmatic Marketing Framework — market-driven product decisions, not feature-driven ones",
    # ── Business Model & Value Creation ──────────────────────────────────────
    "Business Model Canvas (Osterwalder & Pigneur) — nine building blocks of how value is created",
    "Value Proposition Canvas — customer jobs, pains, and gains matched to products and services",
    "Lean Canvas (Ash Maurya) — startup-adapted BMC with problem, solution, unfair advantage",
    "Platform Canvas — extend BMC for multi-sided platform business model design",
    "Profit Pool Analysis (Gadiesh & Gilbert) — map where profit is actually captured in a value chain",
    "Activity System Map (Porter) — visualise how strategic activities reinforce each other",
    "Jobs-Based Business Model Design — design the entire model around the job to be done",
    "Subscription & Recurring Revenue Design — LTV/CAC optimisation, churn architecture",
    "Freemium Model Design — conversion funnel from free to paid; seat expansion logic",
    "Marketplace Business Model — liquidity, matching quality, trust mechanisms, rake",
    "Ecosystem & Platform Orchestration — governance rules, incentives, and developer relations",
    "Razor & Blade Model — subsidise the platform, monetise the consumable",
    "Outcome-Based Pricing — charge for results, not inputs; aligns seller and buyer incentives",
    # ── Systems Thinking & Organisational Design ──────────────────────────────
    "Systems Thinking (Donella Meadows) — stocks, flows, feedback loops, leverage points",
    "Causal Loop Diagrams — map reinforcing and balancing loops in complex systems",
    "Fifth Discipline / Learning Organisation (Senge) — personal mastery, mental models, shared vision",
    "Theory of Constraints (Eliyahu Goldratt) — identify, exploit, and elevate the system constraint",
    "McKinsey 7S Framework — strategy, structure, systems, shared values, skills, style, staff",
    "Galbraith Star Model — strategy, structure, processes, rewards, people; org design framework",
    "Balanced Scorecard (Kaplan & Norton) — financial, customer, process, learning perspectives",
    "OGSM — Objectives, Goals, Strategies, Measures; one-page strategy cascade",
    "Hoshin Kanri (Policy Deployment) — Japanese strategic management, catchball alignment",
    "Lean / Six Sigma / DMAIC — Define, Measure, Analyse, Improve, Control; operational excellence",
    "Agile at Scale / SAFe — coordinate multiple agile teams towards shared business outcomes",
    "Culture Web (Johnson) — stories, symbols, rituals, power, controls, org structure",
    "Psychological Safety (Amy Edmondson) — team learning behaviour and innovation prerequisite",
    "Hofstede's Cultural Dimensions — power distance, individualism, masculinity, uncertainty; global strategy",
    # ── Sustainability, Circular Economy & Social Impact ──────────────────────
    "Circular Economy Framework (Ellen MacArthur Foundation) — eliminate waste, circulate products",
    "Cradle-to-Cradle Design (McDonough & Braungart) — everything is a nutrient; biological or technical cycle",
    "Triple Bottom Line (John Elkington) — People, Planet, Profit; measuring full impact",
    "ESG Framework — Environmental, Social, Governance; investor and stakeholder reporting lens",
    "B Corp Standards — comprehensive impact standards across governance, workers, community, environment",
    "Natural Capitalism (Lovins & Hawken) — resource productivity, biomimicry, service economy",
    "Doughnut Economics (Kate Raworth) — social foundation floor + ecological ceiling; safe space",
    "Stakeholder Capitalism (WEF/Schwab) — value for customers, employees, suppliers, community, shareholders",
    "Impact Business Model (GIIN) — design for positive social/environmental outcomes alongside returns",
    "Theory of Change — map inputs → activities → outputs → outcomes → impact; for social ventures",
    "No specific technique — apply your best professional judgement across disciplines",
    "Other — I'll describe it",
]


# ── Diagnose ──────────────────────────────────────────────────────────────────

class DiagnoseRequest(BaseModel):
    problem: str = Field(..., min_length=10, description="Raw problem statement from the client")
    client_name: str | None = None
    industry: str | None = None
    case_id: str | None = None


class DiagnosisResult(BaseModel):
    case_id: str
    category: str
    severity: str  # low | medium | high | critical
    root_causes: list[str]
    key_questions: list[str]
    recommended_next_step: str
    confidence: float


# ── Intake ────────────────────────────────────────────────────────────────────

class IntakeRequest(BaseModel):
    case_id: str | None = None   # auto-generated if not provided
    raw_input: str = Field(..., min_length=10)
    client_name: str

    # Industry — one of INDUSTRY_OPTIONS; if "Other", populate industry_other
    industry: str
    industry_other: str | None = None

    # Challenges — one or more from CHALLENGE_OPTIONS; if "Other" selected, populate challenges_other
    challenges: list[str] = Field(default_factory=list)
    challenges_other: str | None = None

    # Brand inspiration — select from INSPIRATION_BRAND_OPTIONS; if "Other — I'll describe it", populate inspiration_brand_other
    inspiration_brand_option: str | None = None      # selected item from INSPIRATION_BRAND_OPTIONS
    inspiration_brand_other: str | None = None       # free text when "Other — I'll describe it" is selected
    inspiration_admiration: str | None = None        # what specifically they admire (always free text)

    # Innovation technique or framework — select from INNOVATION_TECHNIQUE_OPTIONS; if "Other — I'll describe it", populate innovation_technique_other
    innovation_technique: str | None = None          # selected item from INNOVATION_TECHNIQUE_OPTIONS
    innovation_technique_other: str | None = None    # free text when "Other — I'll describe it" is selected

    budget_inr: int | None = None
    timeline_weeks: int | None = None


class CaseFile(BaseModel):
    case_id: str
    client_name: str
    industry: str
    challenges: list[str] = Field(default_factory=list)
    inspiration_brand: str | None = None       # resolved label (from dropdown or free text)
    inspiration_admiration: str | None = None
    innovation_technique: str | None = None    # resolved label (from dropdown or free text)
    problem_summary: str
    business_context: str
    target_audience: str
    current_situation: str
    desired_outcome: str
    constraints: list[str]
    success_metrics: list[str]
    priority_level: str  # low | medium | high | urgent
    budget_inr: int | None
    timeline_weeks: int | None


# ── Research ──────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    case_id: str | None = None   # auto-generated if not provided
    query: str = Field(..., min_length=5)
    category: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class Precedent(BaseModel):
    id: str
    title: str
    summary: str
    category: str
    similarity: float
    metadata: dict[str, Any] = {}


class ResearchResult(BaseModel):
    case_id: str
    query: str
    precedents: list[Precedent]
    synthesis_note: str


# ── Synthesize ────────────────────────────────────────────────────────────────

class SynthesizeRequest(BaseModel):
    case_id: str
    case_file: CaseFile | None = None
    research_result: ResearchResult | None = None


class StrategicPillar(BaseModel):
    pillar: str
    rationale: str
    actions: list[str]
    kpis: list[str]


class SynthesisResult(BaseModel):
    case_id: str
    executive_summary: str
    strategic_pillars: list[StrategicPillar]
    quick_wins: list[str]
    risks: list[str]
    recommended_timeline: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
