import pandas as pd
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MFUTransactionImporter:
    """
    Handles importing transactions from MFU entity transaction reports.
    """
    def __init__(self, db):
        self.db = db

    def parse_report(self, file_path):
        """
        Parses an MFU Excel report and returns a list of processed transactions.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Report not found at {file_path}")

        # MFU Header is typically at Index 2
        try:
            df = pd.read_excel(file_path, header=2)
        except Exception as e:
            logger.error(f"Failed to read MFU report: {e}")
            raise

        transactions = []
        for _, row in df.iterrows():
            # Basic validation: must have a value date and a status
            if pd.isna(row.get('Value Date')) or pd.isna(row.get('Transaction Status')):
                continue

            # Only process successfully completed transactions
            status = str(row.get('Transaction Status', '')).strip().lower()
            success_statuses = ['completed', 'settled', 'success', 'rta processed', 'processed']
            if status not in success_statuses:
                continue

            # Map fields
            txn = {
                'order_number': str(row.get('Order Number')),
                'can': str(row.get('CAN')),
                'folio': str(row.get('Folio Number')),
                'rta_code': str(row.get('RTA Scheme Code')),
                'scheme_name': str(row.get('RTA Scheme Name')),
                'amc_name': str(row.get('Fund Name')),
                'type': str(row.get('Transaction Type')),
                'amount': float(row.get('Response Amount')) if pd.notna(row.get('Response Amount')) else 0.0,
                'units': float(row.get('Response Units')) if pd.notna(row.get('Response Units')) else 0.0,
                'nav': float(row.get('Price')) if pd.notna(row.get('Price')) else 0.0,
                'date': row.get('Value Date'),
                'raw_status': status
            }
            
            # Handle timestamps if date is not a datetime object
            if isinstance(txn['date'], str):
                try:
                    txn['date'] = datetime.strptime(txn['date'], '%Y-%m-%d').date()
                except:
                    pass
            elif hasattr(txn['date'], 'date'):
                txn['date'] = txn['date'].date()

            transactions.append(txn)
        
        return transactions

    def process_import(self, transactions):
        """
        Updates the database with the provided transactions.
        """
        results = {
            'total': len(transactions),
            'imported': 0,
            'skipped_duplicate': 0,
            'skipped_no_scheme': 0,
            'skipped_no_client': 0,
            'errors': []
        }

        for txn in transactions:
            try:
                # 1. Resolve Scheme
                scheme = self.db.schemes.get_scheme_by_rta_code(txn['rta_code'])
                
                if not scheme:
                    # Fallback: Create the scheme
                    # Note: We won't have the ISIN (AMFI) code, but we record what we have.
                    try:
                        logger.info(f"Auto-creating scheme: {txn['scheme_name']} (RTA: {txn['rta_code']})")
                        scheme_id = self.db.schemes.add_scheme(
                            scheme_code=None, # ISIN unknown at this stage
                            scheme_name=txn['scheme_name'],
                            rta_code=txn['rta_code']
                        )
                        # Re-fetch or create a mock dict
                        scheme = {'scheme_id': scheme_id}
                        results['auto_created_schemes'] = results.get('auto_created_schemes', 0) + 1
                    except Exception as e:
                        logger.error(f"Failed to auto-create scheme: {e}")
                        results['skipped_no_scheme'] += 1
                        continue
                
                scheme_id = scheme['scheme_id']

                # 2. Resolve Client & CAN
                can_info = self.db.clients.get_can_by_number(txn['can'])
                if not can_info:
                    results['skipped_no_client'] += 1
                    continue
                
                can_id = can_info['can_id']
                client_id = can_info['client_id']

                # 3. Resolve Folio (Create if not exists)
                folio = self.db.folios.get_or_create_folio(can_id, txn['folio'], txn['amc_name'])
                folio_id = folio['folio_id']

                # 4. Map Transaction Type
                # MFU Types: "Add Purchase", "Redemption", "Switch In", "Switch Out", etc.
                crm_type = self._map_txn_type(txn['type'])
                
                # Invert units/amount for Redemptions if they are positive in the sheet
                if crm_type == 'REDEMPTION' and txn['amount'] > 0:
                    # amount/units remain positive in DB but logic should know it's a subtraction
                    # The current app logic likely expects positive numbers and uses 'type' to subtract.
                    pass

                # 5. Add Transaction
                new_id = self.db.transactions.add_transaction(
                    folio_id=folio_id,
                    scheme_id=scheme_id,
                    date=txn['date'].isoformat() if hasattr(txn['date'], 'isoformat') else str(txn['date']),
                    trans_type=crm_type,
                    amount=txn['amount'],
                    units=txn['units'],
                    nav=txn['nav'],
                    order_number=txn['order_number']
                )

                if new_id:
                    results['imported'] += 1
                else:
                    results['skipped_duplicate'] += 1

            except Exception as e:
                logger.error(f"Error importing transaction {txn['order_number']}: {e}")
                results['errors'].append(f"Order {txn['order_number']}: {str(e)}")

        return results

    def _map_txn_type(self, mfu_type):
        """
        Maps MFU transaction types to internal CRM types.
        """
        mt = str(mfu_type).lower()
        if 'purchase' in mt:
            return 'PURCHASE'
        if 'redemption' in mt or 'sell' in mt:
            return 'REDEMPTION'
        if 'sip' in mt:
            return 'SIP'
        if 'swp' in mt:
            return 'SWP'
        if 'stp' in mt or 'switch' in mt:
            # We don't have SWITCH in DB schema yet, mapping switches to PURCHASE/REDEMPTION?
            # Or adding SWITCH?
            # For now, if it's "Switch Out" -> REDEMPTION, "Switch In" -> PURCHASE
            if 'out' in mt: return 'REDEMPTION'
            if 'in' in mt: return 'PURCHASE'
            return 'PURCHASE' # Default
        
        return 'PURCHASE'
