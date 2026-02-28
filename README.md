# Open-MFD CRM

Open-MFD is a free, open-source CRM and Transaction Management tool designed specifically for Mutual Fund Distributors (MFDs) in India. It simplifies client onboarding, portfolio tracking, and customer interaction logging.

## 👑 Governance

This project follows the **BDFL (Benevolent Dictator For Life)** model.

**Current BDFL:** [@rmaries](https://github.com/rmaries)

As the BDFL, @rmaries has final say over the project's direction, feature prioritization, and core architectural decisions. The goal of this model is to ensure a singular, cohesive vision for the software while welcoming contributions from the community.

## 🚀 Key Features
- **Portable Distribution**: No installation required. Runs instantly from a single folder.
- **Client Vault (Encryption)**: Sensitive client data (PAN, Phone, Email, CAN) is encrypted using AES-128.
- **Flexible Onboarding**: Add clients with just Name and Phone. PAN is optional.
- **Document Management**: Securely store and view client photos, PAN copies, and forms (Encrypted on disk).
- **Multiple CAN Support**: Associate multiple Common Account Numbers with a single client profile.
- **Portfolio Tracking**: Real-time XIRR and gain calculations for clients.
- **Client Management**: Edit profile details and KYC status with one click.
- **Interaction Log**: Contextual notes for every meeting and call.
- **Task Engine**: Track pending signatures, KYC updates, and annual reviews.

## 📖 Documentation
Detailed usage instructions can be found in the [USER_GUIDE.md](USER_GUIDE.md).

## 🛠️ Tech Stack
- **Frontend/UI**: Streamlit
- **Database**: SQLite
- **Finance Logic**: Pandas & NumPy Financial

---
*Created and maintained by the MFD community for MFDs.*
