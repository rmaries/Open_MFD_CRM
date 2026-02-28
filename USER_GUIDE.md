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
    - **KYC Toggle**: Quickly update a client's KYC verification status.
    - **Edit Client Profile**: Update Name, PAN, Email, and Phone details.
    - **Notes**: A dedicated space for meeting minutes, complaints, or general interaction logs.
    - **Tasks**: Create and track investor-specific actions.
    - **Documents**: Securely upload, view (images/PDFs), and manage client files (Encrypted on disk).
    - **CAN Numbers**: Manage multiple Common Account Numbers for the same client.
        - The CAN entered during onboarding is **automatically** included here.
        - Click **"➕ Add New CAN Number"** to add additional CANs.
        - Click the **🗑️** icon next to any CAN to remove it.

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
- `FERNET_KEY`: The master encryption key for securing sensitive data (Auto-generated if missing).

  > ⚠️ **Important**: Back up this key securely. If it is lost, all encrypted client data and uploaded documents **cannot be recovered**.
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
