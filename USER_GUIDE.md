# Open-MFD CRM User Guide

Welcome to the Open-MFD CRM. This tool is designed to help Mutual Fund Distributors (MFDs) manage their clients, track investments, and integrate with MFU (Mutual Fund Utilities) seamlessly.

## 🚀 Getting Started

The tool runs in your web browser. When you launch it, you will see a side navigation menu to switch between different sections.

## 📊 1. Dashboard

The Dashboard is your command center, now organized into two primary tabs for better clarity.

### 📊 Distributor Overview
This tab gives you an eagle-eye view of your entire business.
- **Key Metrics**: View your **Total AUM**, **Active Clients** count, **SIP Book**, and **Overdue Tasks** count at a glance.
- **Tasks Overview**: Manage all your actions in one place:
    - **⚠️ Overdue Tasks**: Lists tasks past their due date across all clients.
    - **🕒 Current Tasks**: Displays all 'Pending' and 'In Progress' tasks.
    - **Interactive Updates**: You can update task statuses (e.g., from 'Pending' to 'Completed') directly from these tables. The associated client name is shown for each task.

### 👤 Client Overview
This tab is dedicated to deep-diving into individual client profiles.
1. **Client Selection**: Use the dropdown to select a client.
2. **Portfolio & Interaction Center**:
    - **Portfolio & CANs**: View metrics like Net Investment, Total Gain, XIRR, and detailed holdings.
        - **CAN Selection / Management**: Use the dropdown below the PAN to:
            - View the total aggregate portfolio ("ALL Folios").
            - Filter holdings by a specific CAN.
            - **➕ Add New CAN**: Register a new CAN for the client directly from the dropdown.
            - **⚙️ Manage CANs**: View and delete existing CANs.
    - **Notes**: A dedicated space for meeting logs.
    - **Tasks**: Create and track investor-specific actions. (Updates here are synced with the Distributor Overview).
    - **Documents**: Manage client files.


## 👤 2. Client Management

Use this section to onboard new clients.

- **Full Name \***: Enter the name as it appears in records.
- **Phone Number \***: Mobile or landline contact.
- **PAN**: (Optional) 10-character Permanent Account Number.
- **Email**: (Optional) Contact email address.
- **MFU CAN**: (Optional) Common Account Number.
- **Submit**: Click "Onboard Client" to save.

*\* Required fields for onboarding.*

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
- **Reset Database**: (Warning) This will delete all clients and transactions.

## 🛠️ 6. Advanced Configuration & Portable Build

### Environment Variables (.env)
You can customize the application behavior using the `.env` file in the root directory:
- `DB_PATH`: Specify a custom database file (e.g., `DB_PATH=test_scalability.db`).
- `MFU_API_KEY`: Your credentials for future MFU integration.

### Portable Distribution
To create a "no-install" version of the CRM for another computer:
1. Run `python build_scripts/build_windows.py`.
2. Find the generated ZIP file in the `dist/` folder.
3. Extract and run `Start_CRM.bat` on any Windows PC.

---
## 👑 Project Leadership

This is an open-source project led by its **BDFL (Benevolent Dictator For Life)**, **@rmaries**. 

For support, contributions, or feature requests, please visit the [GitHub repository](https://github.com/rmaries/Open_MFD_CRM).
