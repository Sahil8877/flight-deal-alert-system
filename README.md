
# ✈️ Flight Deal Alert System
An automated flight monitoring system that searches Google Flights for user defined routes, applies price, duration, and layover filters, updates a Google Sheet with the lowest price found, and sends personalised email alerts.

The project demonstrates multi API integration, stateful data persistence, conditional alerting, and production style error handling using Python.

---

## ⚡ At a Glance
| | |
|---|---|
| 🔧 | Fetches user preferences from Google Sheets via Sheety API |
| 🌐 | Searches live flight data using SerpAPI (Google Flights) |
| 🎯 | Filters flights by price, duration, and layover count |
| 📊 | Updates the Google Sheet with the lowest discovered price |
| 📧 | Sends rich HTML email alerts with booking links |
| 🔁 | Designed to run automatically via cron or Task Scheduler |

---

## 📌 Key Features
- 📄 **Google Sheets as a database** stores user targets (origin, destination, max price, max duration, max layovers, departure date) and tracks `lowestPriceFound`
- 🔌 **SerpAPI integration** queries Google Flights for each user on their exact departure date
- ✅ **Smart filtering** accepts a flight only if it meets all user constraints; rejects otherwise
- 💾 **Dynamic price update** when a lower price is found, updates the corresponding row in the sheet via Sheety PUT request
- 📧 **Rich email alerts** include departure/arrival times, layover details (airport, duration, airline, logo), total duration, and a shortened booking link
- 🧹 **Expired flight cleanup** detects past departure dates and deletes the corresponding row from the form responses sheet

---

## 📡 Data Pipeline Architecture
```
Google Sheets (User State Store)
        ↓
Sheety API Ingestion Layer
        ↓
SerpAPI Flight Retrieval Engine
        ↓
Rule-Based Decision Engine
        ↓
State Update Layer (Price Tracking)
        ↓
Notification Engine (HTML Email Builder)
        ↓
SMTP Delivery System
```

---

## ⚙️ Tech Stack
| Tool | Purpose |
|---|---|
| Python 3.x | Core scripting language |
| Sheety API | Read and write Google Sheets as a REST API |
| SerpAPI | Google Flights search endpoint |
| `smtplib` + Gmail | Email delivery |
| `requests` | HTTP calls to Sheety and SerpAPI |
| `pyshorteners` | TinyURL link shortening (with fallback) |
| `dotenv` | Environment variable management |
| `concurrent.futures` | Parallel search execution |

---

## 🧩 Code Structure
The system is split into four main modules, all called from `main.py`:

```
sheets_data.py       → load_targets(): reads user preferences from Google Sheet
flight_search.py     → search_flights(): parallel SerpAPI queries, returns raw results
data_manager.py      → process_flight_deals(): filters flights, updates sheet, builds deal objects
email_manager.py     → build_emails(): constructs HTML per user, handles URL shortening
main.py              → orchestrates all steps, sends emails via SMTP
```

> All functions are import safe – no code runs at import time. Logging is centralised and configurable.

---
## 📊 Example Output (Email HTML)

```html
<h2>✈️ Flight Deals Found For You</h2>
<hr>
<h4>→ Route: London Heathrow (LHR) → Paris Charles de Gaulle (CDG)</h4>
<p><strong>15-May-2025 08:30</strong><br>
🛫 <strong>Departure:</strong> London Heathrow<br>
<img src='https://...airfrance_logo.png' width='20'> <strong>Air France</strong></p>
<p><strong>🛑 Layovers:</strong></p>
<ul>
  <li>Arrival: 10:15<br>↓ <strong>Amsterdam Schiphol (AMS)</strong> (⏱ 1.5 hrs)<br>
  Depart: 11:45 | <img src='...klm_logo.png'> <strong>KLM</strong></li>
</ul>
<p>🛬 <strong>Arrival:</strong> Paris Charles de Gaulle<br>
<strong>15-May-2025 13:30</strong></p>
<p>💰 <strong>£145</strong> | ⏱ 5.0 hrs</p>
<p>🔗 <strong><a href='https://tinyurl.com/...'>Book Now</a></strong></p>
```

---

## 🚀 Getting Started
```bash
# Clone the repository
git clone https://github.com/your-username/flight-deal-alert-system.git
cd flight-deal-alert-system

# Install dependencies
pip install requests python-dotenv pyshorteners serpapi

# Set up environment variables in a .env file
SERP_API_KEY=your_serpapi_key
SHEETS_URL_FLIGHT_DEAL=https://api.sheety.co/.../sheet1
SENDER_EMAIL=your_email@gmail.com
SENDER_EMAIL_PASS=your_app_password

# Run the system
python main.py
```

> ⚠️ The Google Sheet must have columns: `emailAddress`, `departureCode`, `destinationCode`, `priceTarget`, `durationTarget`, `layoverCount`, `departureDate`, `lowestPriceFound`, `id`.  
> Use a cron job (Linux/macOS) or Task Scheduler (Windows) to run `main.py` daily.
