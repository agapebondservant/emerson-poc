**1. Summary**  
The repository is a lightweight ColdFusion web application that aggregates and displays live golf news feeds, tournament leaderboards, and golfer performance data. It exposes a set of HTML pages that pull data from a MySQL‑style database, serializes query results as JSON (via `json.cfc`), and renders them on the client with Prototype, Scriptaculous, and a custom portal widget framework. In addition, it provides demo forms for adding user logins and a debug widget interface.  

---

**2. Components**  

- **`news/add_users.cfm`** – Demo form for entering up to a configured number of user logins; client‑side prototype script collects 6‑character CUIDs into a comma‑separated list.  
- **`news/add_users_mh.cfm`** – Variation of the above with prototype event binding on page load.  
- **`news/debug.cfm`** – Prototype/Scriptaculous widget demo that loads sample news feeds and displays them in draggable widgets.  
- **`news/encode.cfm`** – Mock group creation logic; ingests form values, simulates a database via `QueryNew`, creates a result structure, and returns it as JSON.  
- **`news/encode2.cfm`** – Mock group list generation; returns an array of structures (GroupID, GroupName) as JSON.  
- **`news/getNews.cfm`** – Reads live news stories from the database (`tStories`, `tFeeds`, `tCategories`), builds an array of structs, and outputs JSON.  
- **`news/getNews_mock.cfm`** – Same as above but uses a hard‑coded mock query instead of a database read.  
- **`news/header.cfm`** – Includes page‑level CSS and the shared navigation `tabs.cfm`.  
- **`news/index.cfm`** – Home page that shows ads, the current date, and a placeholder for news widgets.  
- **`news/json.cfc`** – Custom component exposing `encode`, `decode`, and `validate` functions for JSON (legacy).  
- **`news/leaderboards.cfm`** – Stub page that will list tournament leaderboards (currently only header and analytics scripts).  
- **`news/page.cfm`** – General wrapper for news pages including widget containers; identical markup to `index.cfm`.  
- **`news/tabs.cfm`** – Navigation menu shared by the news site; links to “Golf News” and “Leaderboards”.  
- **`pgatour/index.cfm`** – Redirects to the tournaments section (`tournaments/`).  
- **`pgatour/tournaments/header.cfm`** – Page header for tournaments with navigational tabs.  
- **`pgatour/tournaments/index.cfm`** – Main tournaments page; includes a tournament dropdown, AJAX loader for table data, and analytics scripts.  
- **`pgatour/tournaments/index_orig.cfm`** – Original implementation that dumps the tournaments query and displays a simple selector.  
- **`pgatour/tournaments/m_qtournaments.cfm`** – Query that retrieves all tournaments ordered by start date.  
- **`pgatour/tournaments/page.cfm`** – Wrapper page identical to `news/page.cfm`, used for tournament pages.  
- **`pgatour/tournaments/tabs.cfm`** – Navigation tabs for the tournaments site (tournaments and players).  
- **`pgatour/tournaments/ajax_getPlayerData.cfm`** – Server‑side script that receives `playerid`, queries `golfer_history` joined to `golfer` and `events`, builds an HTML table of a golfer’s performance, and returns it.  
- **`pgatour/tournaments/ajax_getTourney.cfm`** – Server‑side script that receives `tourneyid`, queries `golfer_history` joined to `golfer` and `events`, builds an HTML table of a tournament leaderboard, and returns it.  
- **`pgatour/tournaments/getNews.cfm`** – Same news‑feed retrieval logic as `news/getNews.cfm`, but in the tournaments namespace.  
- **`pgatour/tournaments/players.cfm`** – Dropdown for selecting a golfer; AJAX calls `ajax_getPlayerData.cfm` to show that golfer’s history.  
- **`json.cfc`** – Custom component for encoding/decoding JSON and validating against a schema (not used elsewhere in the current code).

---

**3. Conceptual Domain**  

- **User / Login** – Represents a user login; mock logic in `encode.cfm`/`encode2.cfm`.  
- **Group** – A collection of users; created in `encode.cfm`.  
- **News Feed** – External RSS/Atom feeds providing golf news.  
- **Story** – Individual news item with title, link, summary; table `tStories`.  
- **Category** – Classification of stories (e.g., tournament, travel); table `tCategories`.  
- **Tournament** – A golf event; joined data from `events`, `event_names`, `golfer_history`.  
- **Golfer** – Player with first and last name; table `golfer`.  
- **GolferHistory** – Performance records for a golfer in a specific tournament; table `golfer_history`.  

These concepts map loosely to the domain of a golf information portal where stories, tournament results, and player statistics are displayed to the user.

---

**4. Physical Domain**  

- **Database `golfap`** (DSN `golfap`) contains:  
  - `tFeeds (feedID, categoryID, ...)` – feeds metadata.  
  - `tCategories (categoryID, categoryName)` – category lookup.  
  - `tStories (storyID, feedID, link, title, summary, ...)` – stored news stories.  
  - `golfer (id, fname, lname)` – golfer master record.  
  - `golfer_history (id, golfer_id, event_id, to_par, thru, r1, r2, r3, r4, total, today, pos, madecut, ...)` – performance histories.  
  - `events (id, name, start_date, dates, ...)` – tournament event data.  
  - `event_names (id, name)` – human‑readable event names.  
- **Query aliases used in code**:  
  - `qtournaments` – result from `m_qtournaments.cfm`.  
  - `qGetNews`, `qGetThisGroup`, `qGetAllGroups` – temporary query objects for JSON responses.  
  - `qPlayerInfo` / `qThisTourney` – query results for displaying tables.

The application relies on these tables to assemble JSON arrays and HTML tables for presenting news, tournaments, and golfer information.