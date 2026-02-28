from enum import Enum

class TransactionType(str, Enum):
    """Types of financial transactions in the CRM."""
    PURCHASE = "PURCHASE"
    REDEMPTION = "REDEMPTION"
    SIP = "SIP"
    STP = "STP"
    SWP = "SWP"

class TaskStatus(str, Enum):
    """Lifecycle status of a CRM task."""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class Priority(str, Enum):
    """Priority levels for tasks."""
    HIGH = "High"
    MED = "Med"
    LOW = "Low"

class DocumentType(str, Enum):
    """Categories for uploaded client documents."""
    PHOTO = "Photo"
    PAN_COPY = "PAN Copy"
    MASKED_AADHAAR = "Masked Aadhaar"
    AADHAAR_XML = "Aadhaar xml"
    BANK_PROOF = "Bank Proof"
    PASSPORT_COPY = "Passport Copy"
    SCANNED_SIGNATURE = "Scanned Signature"
    OTHER = "Other"
