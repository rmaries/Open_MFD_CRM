# Open-MFD CRM User Guide

Welcome to the Open-MFD CRM. This tool is designed to help Mutual Fund Distributors (MFDs) manage their clients, track investments, and integrate with MFU (Mutual Fund Utilities) seamlessly.

## 🚀 Getting Started

The tool runs in your web browser. When you launch it, you will see a side navigation menu to switch between different sections.

## 📊 1. Dashboard

The Dashboard is your command center. It gives you an eagle-eye view of your business.

- **Total AUM**: The current aggregate market value of all assets under your management.
- **Active Clients**: Total number of unique clients onboarded in the system.
- **SIP Book (Monthly)**: (Upcoming) Monthly SIP inflow tracking.
- **Overdue Tasks**: Highlights the count of tasks that have passed their due date.
- **Client List**: A searchable table of all your clients and their KYC status.
- **Portfolio & Interaction Center**: Select a specific client to view their detailed profile:
    - **Portfolio**: View metrics like Net Investment, Total Gain, XIRR, and detailed holdings.
    - **Notes**: A dedicated space for meeting minutes, complaints, or general interaction logs with search capabilities.
    - **Tasks**: Create and track investor-specific actions (e.g., "Get signature"). Use the **Standard MFD Task** templates for recurring reviews.

## 👤 2. Client Management

Use this section to onboard new clients.

- **Full Name**: Enter the name exactly as it appears on the client's PAN card.
- **PAN**: 10-character Permanent Account Number.
- **Email/Phone**: Contact details for the client.
- **MFU CAN**: (Optional) Common Account Number if the client is already registered with MFU.
- **Submit**: Click "Onboard Client" to save.

## 📈 3. Investment Tracking

This section allows you to record physical or digital transactions.

1.  **Select Client**: Choose from the list of onboarded clients.
2.  **Folio Management**:
    - Select an existing folio or click **"Add New Folio"**.
    - For new folios, provide the Folio Number and the AMC Name (e.g., SBI Mutual Fund).
3.  **Record Transaction**:
    - **Scheme**: Select the mutual fund scheme.
    - **Transaction Type**: Choose from PURCHASE, REDEMPTION, SIP, STP, SWP.
    - **Amount/NAV**: Enter the transaction amount and the NAV on that date.
    - **Submit**: Click "Submit Transaction" to update the portfolio.

## 🔗 4. MFU Integration

This section is dedicated to connecting with MFU APIs. 
- *Current Status*: This feature is under development. Once active, it will allow you to pull client data and transactions directly from MFU.

## ⚙️ 5. Settings

- View your local database path.
- **Reset Database**: (Warning) This will delete all clients and transactions. Use this only for demo purposes or starting fresh.

---
*For support or contributions, please check the project repository.*
