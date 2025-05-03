# DatabaseActor (runs on database_server):

# Setup: Get own mailbox.
# Loop:
# Wait for and receive a query (query_data = mailbox->get()). Get requesting ProcessingActor.
# Extract Face ID and Zone ID from query_data.
# Simulate Database Lookup & Access Rule Check:
# Define computational cost (flops_db_lookup).
# Execute computation (simgrid::s4u::this_actor::execute(flops_db_lookup)).
# Apply Rules (Internal Logic): Implement the logic here. This is where the rules live. Based on the received Face ID and Zone ID, determine if access is granted (e.g., check against an internal data structure representing authorized personnel per zone).
# Create response payload ("Authorized" / "Unauthorized"). Define size (very small, e.g., 100 bytes).
# Send response back to the requesting ProcessingActor's mailbox (reply_mailbox->put(response_data, response_size)).

# TODO: 
# Based on the received Face ID and Zone ID, determine if access is granted 
# (e.g., check against an internal data structure representing authorized personnel per zone).   
# Implement the other functions as needed.

from simgrid import Mailbox, this_actor, SimgridError, Engine

class DatabaseActor:
    def __init__(self, database_server: str, processing_mailbox_name: str):
        """
        database_server: Name of the database server.
        processing_mailbox_name: Mailbox name of the ProcessingActor.
        """
        
        self.database_server = database_server
        self.database_mailbox = Mailbox.by_name(database_server)
        self.processing_mailbox_name = processing_mailbox_name
        
        try:
            self.processing_mailbox = Mailbox.by_name(self.processing_mailbox_name)
            
        except SimgridError as e:
            this_actor.error(f"Mailbox {self.processing_mailbox_name} not found for database server {self.database_server}.")
        
     
    def __call__(self, face_id: str, zone_id: str):
        this_actor.info(f"Looking up Face ID {face_id} for Zone ID {zone_id} at {Engine.clock:.3f}")
        
        flops_db = 1000       
        
        try:
            #  cost for a lookup is significantly lower than your OD/FR costs. The key is that the system doesn't grind to a halt waiting for serial database checks.
            this_actor.execute(flops_db)
            
            face_id = self.simulate_lookup()
            
            self.processing_mailbox.put(face_id)
            
        except SimgridError as e:
            this_actor.error(f"Error during facial recognition: {e}")        
         
        return face_id   