# Project Context: MFD CRM (Modular Python/Streamlit)

## 🎯 Project Overview
An open-source CRM for Mutual Fund Distributors.
- **Primary Stack:** Python 3.12+, Streamlit (UI), SQLite (Database).
- **Key Identifier:** ARN-151461 (Must be visible in all UI modules).
- **Compliance:** Adheres to SEBI/AMFI data privacy and disclosure norms.

## 📂 Directory Map (High-Level)
- `app.py`: Main entry point and Streamlit sidebar/navigation.
- `src/modules/`: 
    - `auth.py`: User session and login logic.
    - `clients.py`: CRUD operations for client profiles.
    - `portfolio.py`: Integration with RTA data/valuation logic.
    - `compliance.py`: Generates mandatory disclosures.
- `src/utils/`: Shared helper functions (Date formatting, SQLite wrappers).
- `data/`: Local SQLite database storage.
- `build_scripts/`: Scripts for freezing into Win/Linux executables.

## 💾 Core State (st.session_state)
*To maintain consistency across modules, use these keys:*
- `user_authenticated`: Boolean (True/False).
- `current_client_id`: ID of the currently selected client.
- `active_module`: Tracks which page is currently rendered.
- `db_connection`: Persistent SQLite connection object.

## 🗄️ Database Schema (Primary Tables)
- **clients:** `id` (PK), `name`, `pan`, `email`, `mobile`, `created_at`.
- **transactions:** `id` (PK), `client_id` (FK), `scheme_name`, `amount`, `date`.

## 📜 Development Guardrails
1. **Persistence:** Always commit SQLite transactions immediately to prevent data loss on script reruns.
2. **Modularity:** UI code stays in `app.py` or specific UI functions; business logic must live in `src/modules/`.