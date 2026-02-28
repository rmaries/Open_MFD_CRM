from src.modules.db.database import Database
import os

def test_can_deletion():
    db = Database()
    
    # 1. Create a test client and CAN
    client_id = db.add_client(name="Test Deletion", pan="ABCDE1234F")
    can_number = "1234567890"
    can_id = db.add_client_can(client_id, can_number)
    print(f"Created CAN {can_id} for client {client_id}")
    
    # 2. Try to delete the empty CAN
    success, message = db.delete_client_can(can_id)
    print(f"Deletion 1 (Empty CAN): Success={success}, Message='{message}'")
    assert success == True
    
    # 3. Create another CAN and add a folio to it
    can_id_2 = db.add_client_can(client_id, "0987654321")
    db.add_folio(can_id_2, "FOLIO123", "Test AMC")
    print(f"Created CAN {can_id_2} and added a folio.")
    
    # 4. Try to delete the CAN with a folio
    success_2, message_2 = db.delete_client_can(can_id_2)
    print(f"Deletion 2 (CAN with folio): Success={success_2}, Message='{message_2}'")
    assert success_2 == False
    assert "Cannot delete" in message_2
    
    print("Verification Successful!")

if __name__ == "__main__":
    test_can_deletion()
