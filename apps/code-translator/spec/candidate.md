**1. Summary**  
Golfap is a social golf score‑keeping web application that lets users track scores, place bets, and manage games with friends.  It presents news feeds, leaderboards, and PGA‑tour tournament data, and it uses ColdFusion pages rendered from Markdown templates.  The application serialises data to JSON for AJAX calls, validates input, and integrates Google AdSense and Google Analytics for monetisation and tracking.  The code base is organised into a *news* module, a *pgatour* module, and a shared *tabs* component.  The application relies on a ColdFusion datasource named **GOLFAP** to query tournament, player, news, and score data.  The code is valid ColdFusion/Markdown and follows a typical MVC pattern with reusable templates and custom helper functions.  [Data: Reports (73, 173, 117, 175, 80)]

---

**2. Components**  

*Primary Modules*  
- `news/add_users.md` – handles user registration and group creation.  
- `news/add_users_mh.md` – helper for adding users.  
- `news/debug.md` – debugging utilities for the news module.  
- `news/encode.md` – defines `VAL()` and `ENCODE()` functions for input sanitisation.  
- `news/encode2.md` – additional encoding helpers.  
- `news/getNews.md` – retrieves news items via `QGETNEWS_QUERY`.  
- `news/getNews_mock.md` – provides mock news data for testing.  
- `news/header.md` – reusable header markup, includes `OBJECT PAGE_TRACKER` for analytics.  
- `news/index.md` – landing page for the news section.  
- `news/json.md` – defines `jsonEncode()` and `jsonDecode()` functions.  
- `news/leaderboards.md` – renders global leaderboard tables.  
- `news/page.md` – wrapper page for news content, includes `PAGE_TRACKER` and `ANALYTICSTRACKER`.  
- `news/tabs.md` – reusable tab navigation component.  
- `pgatour/index.md` – landing page for PGA‑tour data.  
- `pgatour/tournaments/ajax_getPlayerData.md` – AJAX endpoint returning player statistics in JSON.  
- `pgatour/tournaments/ajax_getTourney.md` – AJAX endpoint returning tournament details in JSON.  
- `pgatour/tournaments/getNews.md` – retrieves news specific to tournaments.  
- `pgatour/tournaments/header.md` – header template for tournament pages.  
- `pgatour/tournaments/index.md` – main tournament listing page.  
- `pgatour/tournaments/index_orig.md` – original version of the tournament index.  
- `pgatour/tournaments/m_qtournaments.md` – query helper for quick tournament data (`QTournaments`).  
- `pgatour/tournaments/page.md` – wrapper page for tournament content.  
- `pgatour/tournaments/players.md` – displays player profiles and statistics.  
- `pgatour/tournaments/tabs.md` – tab navigation for tournament pages.  
- `tabs.md` – global tab navigation component used by both modules.  

*Primary Web Pages*  
- `news/index.md` – home page for news and leaderboards.  
- `news/page.md` – generic page template for news content.  
- `news/leaderboards.md` – leaderboard view.  
- `pgatour/index.md` – PGA‑tour overview page.  
- `pgatour/tournaments/index.md` – detailed tournament list.  
- `pgatour/tournaments/page.md` – detailed tournament view.  
- `pgatour/tournaments/players.md` – player profile view.  

*ColdFusion Components*  
- `CFQUERY QGETNEWS_QUERY` – retrieves news articles.  
- `CFQUERY QGETNEWS` – used in `news/getNews.md`.  
- `CFQUERY QPLAYERS` – retrieves player data.  
- `CFQUERY QTournaments` – retrieves tournament data.  
- `CFQUERY QGETALLGROUPS` – retrieves group information.  
- `CFQUERY QMOCK` – mock data for testing.  
- `CFQUERY QTHISTOURNEY_QUERY` – historical tournament data.  
- `CFOUTPUT` – renders query results into HTML.  
- `CFSET` – assigns variables such as `TOURNAMENT_ID`.  
- `CFLOOP` – generates login input fields in `add_users.md`.  
- `CFIF`, `CFELSEIF`, `CFELSE` – conditional logic.  
- `CFINCLUDE` – includes `header.md`, `tabs.md`, and other templates.  
- `CFINVOKE` – serialises data to JSON via `jsonEncode()`.  

*Reusable Templates*  
- `news/header.md` – common header markup, includes analytics scripts.  
- `news/tabs.md` – tab navigation component.  
- `news/page.md` – page wrapper for news content.  
- `pgatour/tournaments/header.md` – header for tournament pages.  
- `pgatour/tournaments/tabs.md` – tab navigation for tournament pages.  
- `tabs.md` – global tab navigation component.  

*Custom Components & Functions*  
- `COMPONENT JSON` (defined in `news/json.md`) – provides `jsonEncode()` and `jsonDecode()`.  
- `ENCODE()` (defined in `news/encode.md`) – custom encoding helper.  
- `VAL()` (defined in `news/encode.md`) – input sanitisation helper.  
- `PAGE_TRACKER` (defined in `news/page.md`) – Google Analytics tracker.  
- `ANALYTICSTRACKER` (defined in `news/page.md`) – analytics helper.  
- `OBJECT PAGE_TRACKER` (in `news/header.md`) – analytics script inclusion.  
- `AD_CONFIGURATION` (in `news/header.md`) – Google AdSense configuration.  

[Data: Reports (99, 71, 230, 148, 210)]  
[Data: Reports (143, 291, 264, 213, 289)]  

---

**3. Conceptual Domain**  

- **User** – represents a golfer or fan who can log in, track scores, place bets, and view news.  
- **Player** – a golfer whose personal and performance data is stored in the `GOLFER` table and displayed via `pgatour/tournaments/players.md`.  
- **Tournament** – an event defined in the `EVENTS` and `EVENT_NAMES` tables; accessed through `QTournaments` and displayed in `pgatour/tournaments/index.md`.  
- **NewsArticle** – a news item stored in the `NEWS` table; retrieved by `QGETNEWS_QUERY` and rendered in `news/getNews.md`.  
- **LeaderboardEntry** – aggregates a player's score for a tournament; displayed in `news/leaderboards.md`.  
- **Bet** – a wager between users on a tournament outcome; implied by the application description but not explicitly modelled in the current code.  
- **Game** – a collection of scores and bets for a session; implied by the application description but not explicitly modelled.  

The current state of the domain objects is that **Users** are created via `add_users.md`, **Players** and **Tournaments** are queried from the database and presented through AJAX endpoints, **NewsArticles** are fetched and displayed in the news section, and **LeaderboardEntries** are rendered from query results.  Bets and Games are not yet persisted in the code base.  

[Data: Reports (21, 55, 11, 229, 162)]  

---

**4. Physical Domain**  

- **Datasource** – `GOLFAP` (or `GOLFAP_DATASOURCE`) is the ColdFusion datasource used for all queries.  
- **Database Tables**  
  - `GOLFER` – stores golfer personal data.  
  - `GOLFER_HISTORY` – stores historical scores per golfer.  
  - `EVENTS` – stores tournament event records.  
  - `EVENT_NAMES` – maps event IDs to human‑readable names.  
  - `TSTORIES` – stores news story data.  
  - `TFEEDS` – stores news feed data.  
  - `TCATEGORIES` – stores news categories.  
  - `TPLAYERS` – stores player data.  
  - `TTOURNAMENTS` – stores tournament data.  
  - `TSCORERS` – stores individual scores per tournament.  
- **ColdFusion Components** – CFQUERY tags (`QGETNEWS_QUERY`, `QGETNEWS`, `QPLAYERS`, `QTournaments`, `QGETALLGROUPS`, `QMOCK`, `QTHISTOURNEY_QUERY`) access the tables above.  
- **AJAX Endpoints** – `ajax_getPlayerData.md` and `ajax_getTourney.md` return JSON data for players and tournaments.  
- **Client‑Side Assets** – Prototype.js, Effects, Builder, DragDrop, Portal, Firebug, and custom JavaScript for dynamic UI updates.  
- **Ad & Analytics** – Google AdSense scripts are injected via `AD_CONFIGURATION` in `news/header.md`; Google Analytics tracking is included through `OBJECT PAGE_TRACKER` and `PAGE_TRACKER`.  

The physical domain is a typical ColdFusion web application that serves Markdown‑rendered pages, uses a relational database for persistence, and provides dynamic content via AJAX and JSON.