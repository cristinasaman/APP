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

from simgrid import Mailbox, this_actor, SimgridError, Engine, Host
import random

class DatabaseActor:
    def __init__(self, database_server: str, processing_mailbox_name: str):
        """
        database_server: Name of the database server.
        processing_mailbox_name: Mailbox name of the ProcessingActor.
        """
        
        self.database_server = database_server
        self.database_mailbox = Mailbox.by_name(database_server)
        self.processing_mailbox_name = processing_mailbox_name
        
        # Extragerea resurselor computaționale disponibile
        try:
            host = Host.by_name(database_server)
            self.host_speed = host.speed  # Viteza de procesare în FLOPS
        except Exception as e:
            this_actor.error(f"Nu s-a putut obține informații despre host: {e}")
            self.host_speed = 1e9  # Valoare default 1 GFlops
        
        # Calculăm capacitatea de procesare a cererilor în paralel
        if self.host_speed >= 1e11:  # 100 GFlops sau mai mult
            self.query_parallelism = 4  # Procesează mai multe cereri în paralel
        else:
            self.query_parallelism = 1  # Procesare serială
        
        # Inițializăm mailbox-ul pentru procesare (opțional, doar pentru compatibilitate cu codul anterior)
        try:
            self.processing_mailbox = Mailbox.by_name(self.processing_mailbox_name)
        except SimgridError as e:
            this_actor.warning(f"Mailbox {self.processing_mailbox_name} not found. This is fine in a distributed environment.")
            self.processing_mailbox = None
        
        # Inițializăm baza de date cu reguli de acces
        self.init_access_rules()
        
        this_actor.info(f"DatabaseActor initialized on {database_server} with capacity {self.host_speed/1e9:.2f} GFlops")
    
    def __call__(self):
        """
        Main function of the database actor.
        Receives and processes authorization queries.
        """
        this_actor.info(f"Started database server on {self.database_server}. Waiting for queries at {Engine.clock:.3f}")
        
        while True:
            try:
                # Primește o cerere de la un actor de procesare
                query = self.database_mailbox.get()
                this_actor.info(f"Received query: {query} at {Engine.clock:.3f}")
                
                # Parsează cererea pentru a extrage informațiile necesare
                face_id, zone_id, reply_mailbox_name = self.parse_query(query)
                
                # Verifică dacă mailbox-ul de răspuns există
                try:
                    reply_mailbox = Mailbox.by_name(reply_mailbox_name)
                except SimgridError as e:
                    this_actor.error(f"Mailbox {reply_mailbox_name} not found for reply. Query: {query}")
                    continue
                
                # Simulează costul computațional al interogării bazei de date
                # Costul este împărțit în funcție de capacitatea de paralelizare
                query_flops = 1000  # Cost de bază pentru o interogare
                this_actor.execute(query_flops / self.query_parallelism)
                
                # Verifică autorizarea
                authorized = self.check_authorization(face_id, zone_id)
                
                # Trimite răspunsul înapoi la nodul de procesare
                response = "Authorized" if authorized else "Unauthorized"
                this_actor.info(f"Sending response: {response} for Face ID: {face_id}, Zone: {zone_id} to {reply_mailbox_name}")
                reply_mailbox.put(response, 100)  # 100 bytes pentru răspuns
                
            except SimgridError as e:
                this_actor.error(f"Error while processing query: {e}")
                # Nu ieșim din buclă pentru a permite sistemului să continue
                continue
    
    def parse_query(self, query):
        """
        Parsează cererea primită pentru a extrage informațiile necesare.
        Format așteptat: "Query: {face_id}, Zone ID: {zone_id},{reply_mailbox}"
        """
        try:
            # Separă componentele cererii
            query_parts = query.split(',')
            
            # Extrage reply_mailbox (ultimul element)
            reply_mailbox = query_parts[-1].strip()
            
            # Extrage face_id din prima parte
            face_id_part = query_parts[0]
            face_id = face_id_part.split("Query:")[1].strip()
            
            # Extrage zone_id din a doua parte
            zone_id_part = query_parts[1]
            zone_id = zone_id_part.split("Zone ID:")[1].strip()
            
            return face_id, zone_id, reply_mailbox
            
        except (IndexError, ValueError) as e:
            this_actor.error(f"Failed to parse query: {query}. Error: {e}")
            # Valori default în caz de eroare
            return "unknown_face", "unknown_zone", self.processing_mailbox_name
    
    def init_access_rules(self):
        """
        Inițializează regulile de acces pentru diferite zone și utilizatori.
        """
        # Structura de reguli: {zone_id: {user_type_prefix: is_authorized}}
        self.access_rules = {
            "zone_1": {
                "zone1_employee_": True,
                "zone1_visitor_": False,
                "zone1_manager_": True,
                "zone1_security_": True,
                "unknown_person_": False,
                # Default pentru alte tipuri
                "default": False
            },
            # Regulă default pentru zone necunoscute
            "default": {
                "default": False
            }
        }
        
        # Liste de utilizatori specifici cu acces special (override)
        self.special_users = {
            # Utilizatori cu acces blocat în toate zonele (ex: foști angajați)
            "blacklist": [
                "zone1_employee_042",
                "zone1_visitor_013"
            ],
            # Utilizatori cu acces în toate zonele (ex: CEO, șefi securitate)
            "whitelist": [
                "zone1_manager_001",
                "zone1_security_007"
            ]
        }
    
    def check_authorization(self, face_id, zone_id):
        """
        Verifică dacă un utilizator (face_id) are acces la o zonă specifică.
        """
        # Verifică liste speciale mai întâi
        if face_id in self.special_users["blacklist"]:
            this_actor.info(f"Access DENIED for {face_id} (blacklisted user)")
            return False
            
        if face_id in self.special_users["whitelist"]:
            this_actor.info(f"Access GRANTED for {face_id} (whitelisted user)")
            return True
        
        # Verifică regulile pentru zonă
        zone_rules = self.access_rules.get(zone_id, self.access_rules["default"])
        
        # Caută prefixul potrivit pentru face_id
        for prefix, is_authorized in zone_rules.items():
            if prefix != "default" and face_id.startswith(prefix):
                if is_authorized:
                    this_actor.info(f"Access GRANTED for {face_id} in zone {zone_id} (rule: {prefix})")
                else:
                    this_actor.info(f"Access DENIED for {face_id} in zone {zone_id} (rule: {prefix})")
                return is_authorized
        
        # Dacă nu a găsit nicio regulă specifică, aplică regula default pentru zonă
        this_actor.info(f"No specific rule found for {face_id} in {zone_id}. Using default: {zone_rules['default']}")
        return zone_rules["default"]
    
    # Implementare pentru compatibilitate cu versiunea anterioară
    def simulate_lookup(self):
        """
        Simulează căutarea în baza de date.
        Menținută pentru compatibilitate cu implementarea anterioară.
        """
        face_ids = ["zone1_employee_001", "zone1_visitor_002", "zone1_manager_003", "unknown_face"]
