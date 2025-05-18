# APP/actors/database_actor.py
from simgrid import Mailbox, this_actor, Engine # Host might not be needed unless for dynamic speed adjust
import random

class DatabaseActor:
    def __init__(self, my_mailbox_name: str): # Renamed parameter
        """
        my_mailbox_name: The mailbox name this DatabaseActor will listen on.
        """
        self.my_mailbox_name = my_mailbox_name
        try:
            self.mailbox = Mailbox.by_name(self.my_mailbox_name)
        except Exception as e:
            this_actor.error(f"Failed to get own mailbox '{self.my_mailbox_name}'. Actor cannot start.")
            raise e
        
        # Computational cost for a single lookup/authorization check
        self.db_lookup_flops = 200e6  # Example: 200 MFLOPS (can be tuned)
        # Optional: Simulate DB's internal parallelism capability
        # self.query_parallelism_factor = 4 # Number of queries it can "conceptually" handle in parallel
                                      # Cost executed would be self.db_lookup_flops / self.query_parallelism_factor

        self.init_access_rules() # Initialize the simulated database rules
        
        this_actor.info(f"DatabaseActor initialized. Listening on '{self.my_mailbox_name}'.")

    def init_access_rules(self):
        """Initializes the simulated access rules database."""
        # Your existing access_rules and special_users structure is good.
        # Ensure it covers all zones you plan to simulate (zone_1, zone_2, zone_3).
        self.access_rules = {
            "zone_1": {
                "zone1_employee_": True, "zone1_visitor_": False, "zone1_manager_": True,
                "zone1_security_": True, "unknown_person_": False, "unknown_face": False,
                "low_confidence_face": False, "default": False
            },
            "zone_2": { # Example rules for zone_2
                "zone2_employee_": True, "zone2_manager_": True, "zone1_security_": True, # Security might have wider access
                "unknown_person_": False, "unknown_face": False, "low_confidence_face": False,
                "default": False
            },
            "zone_3": { # Example rules for zone_3
                "zone3_employee_": True, "zone3_security_": True, "zone1_manager_": True, # Managers might have wider access
                "unknown_person_": False, "unknown_face": False, "low_confidence_face": False,
                "default": False
            },
            "default": {"default": False} # Default for unknown zones
        }
        self.special_users = {
            "blacklist": ["zone1_employee_042", "zone1_visitor_013"],
            "whitelist": ["zone1_manager_001", "zone1_security_007"] # These users are authorized everywhere
        }
        this_actor.info("Access rules initialized.")

    def check_authorization(self, face_id: str, zone_id: str) -> bool:
        """Checks if a face_id is authorized for a given zone_id."""
        if not face_id: # Handle None or empty face_id
            this_actor.info(f"Authorization check for EMPTY FaceID in Zone '{zone_id}' -> DENIED (default)")
            return False
            
        # 1. Check special lists (blacklist overrides whitelist if user is on both, though unlikely)
        if face_id in self.special_users["blacklist"]:
            this_actor.info(f"Access DENIED for '{face_id}' in Zone '{zone_id}' (blacklisted).")
            return False
        if face_id in self.special_users["whitelist"]:
            this_actor.info(f"Access GRANTED for '{face_id}' in Zone '{zone_id}' (whitelisted).")
            return True
        
        # 2. Get rules for the specific zone, or default zone rules if zone not found
        zone_specific_rules = self.access_rules.get(zone_id, self.access_rules["default"])
        
        # 3. Check against prefixes in the zone rules
        for prefix, is_authorized in zone_specific_rules.items():
            if prefix != "default" and face_id.startswith(prefix):
                log_status = "GRANTED" if is_authorized else "DENIED"
                this_actor.info(f"Access {log_status} for '{face_id}' in Zone '{zone_id}' (rule: '{prefix}').")
                return is_authorized
                
        # 4. If no specific prefix matched, apply the zone's default rule
        default_auth = zone_specific_rules.get("default", False)
        log_status = "GRANTED" if default_auth else "DENIED"
        this_actor.info(f"No specific rule for '{face_id}' in Zone '{zone_id}'. Applying zone default: {log_status}.")
        return default_auth

    def __call__(self):
        this_actor.info(f"Started. Waiting for queries on '{self.my_mailbox_name}'.")
        while True:
            try:
                # Expecting a dictionary query from ProcessingActorCPU
                query_message = self.mailbox.get()

                if not isinstance(query_message, dict) or query_message.get("type") != "auth_query":
                    this_actor.warning(f"Received malformed or unexpected query type: {query_message}")
                    continue

                face_id = query_message.get("face_id")
                zone_id = query_message.get("zone_id")
                reply_to_mailbox_name = query_message.get("reply_to_mailbox")

                if not all([face_id, zone_id, reply_to_mailbox_name]):
                    this_actor.error(f"Incomplete query received: {query_message}. Missing required fields.")
                    # Optionally send an error response back if reply_to_mailbox_name is present
                    if reply_to_mailbox_name:
                        try:
                            error_response = {"type": "auth_result", "status": "Error_BadRequest", "queried_face_id": face_id, "queried_zone_id": zone_id}
                            Mailbox.by_name(reply_to_mailbox_name).put(error_response, 100)
                        except Exception as e_err_reply:
                            this_actor.error(f"Failed to send error reply for bad query to {reply_to_mailbox_name}: {e_err_reply}")
                    continue
                
                this_actor.info(f"Received query: FaceID='{face_id}', Zone='{zone_id}'. Reply to='{reply_to_mailbox_name}'.")

                # Simulate DB lookup and rule processing cost
                # You can add / self.query_parallelism_factor here if defined and desired
                this_actor.execute(self.db_lookup_flops) 

                authorized = self.check_authorization(face_id, zone_id)
                
                response_status = "Authorized" if authorized else "Unauthorized"
                response_payload = {
                    "type": "auth_result", # Important for ProcessingActorCPU to identify the message
                    "status": response_status,
                    "queried_face_id": face_id, # Echoing back for context
                    "queried_zone_id": zone_id
                }
                
                try:
                    reply_mailbox = Mailbox.by_name(reply_to_mailbox_name)
                    # Size of the response dictionary (SimGrid will estimate if payload is object)
                    # Let's use a small fixed size for this structured message.
                    reply_mailbox.put(response_payload, 256) 
                    this_actor.info(f"Sent response '{response_status}' for FaceID:'{face_id}', Zone:'{zone_id}' to '{reply_to_mailbox_name}'.")
                except Exception as e_reply:
                    this_actor.error(f"Failed to get reply mailbox '{reply_to_mailbox_name}' or send reply: {e_reply}")

            except Exception as e:
                this_actor.error(f"DatabaseActor error in main loop: {e}")
                break # Exit loop on SimgridError
            except Exception as e_gen: # Catch any other unexpected errors
                this_actor.error(f"DatabaseActor UNEXPECTED error in main loop: {e_gen}")
                # break or continue
        this_actor.info("DatabaseActor stopping.")