"""
Services for external integrations and data synchronization.
"""
from .external_api import ExternalJournalAPI
from .data_mapper import ExternalDataMapper

__all__ = ['ExternalJournalAPI', 'ExternalDataMapper']
