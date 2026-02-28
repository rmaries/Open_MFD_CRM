"""
Backward-compatibility shim. 
Exposes components from the new modular structure to existing callers.
"""
from .client_form import input_client_details
from .transaction_form import transaction_entry
from .notes_view import render_notes_section
from .tasks_view import render_tasks_section
from .documents_view import render_documents_section
from .can_management import render_can_management
