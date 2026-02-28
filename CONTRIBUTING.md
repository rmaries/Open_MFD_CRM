# Contributing to Open-MFD CRM

Thank you for your interest in contributing! Open-MFD is a community-driven project aimed at helping Mutual Fund Distributors (MFDs) in India.

## ⚖️ Governance Note

This project follows the **BDFL (Benevolent Dictator For Life)** model. All final decisions regarding features and architecture are made by the BDFL ([@rmaries](https://github.com/rmaries)).

## 🛠️ How to Contribute

### 1. Reporting Bugs
- Check the [Issues](https://github.com/rmaries/Open_MFD_CRM/issues) tab to see if the bug has already been reported.
- If not, create a new issue with a clear description, steps to reproduce, and screenshots if applicable.

### 2. Suggesting Features
- We welcome ideas! Please open an issue to discuss your feature suggestion before starting development.

### 3. Submitting Changes (Pull Requests)
- Fork the repository.
- Create a new branch for your feature or bugfix (`git checkout -b feature/awesome-new-thing`).
- Commit your changes with descriptive messages.
- **Run the verification scripts** (see `DEVELOPER_GUIDE.md`) to ensure no regressions.
- Push to your fork and submit a Pull Request.

## 🎨 Coding Standards

- **Python**: Follow PEP 8 guidelines for clean code.
- **Streamlit**: Keep UI logic separated into `src/ui/components.py` and business logic in `src/modules/`.
- **Security**: Never store sensitive data in plain text. Always use the `Database._encrypt` and `Database._decrypt` methods.
- **Consistency**: Use the existing design language (Streamlit columns, metrics, and containers) to keep the UI feel cohesive.

## 🛡️ License

By contributing to Open-MFD CRM, you agree that your contributions will be licensed under the project's open-source license.
