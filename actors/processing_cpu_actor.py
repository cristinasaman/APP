# In APP/actors/processing_cpu_actor.py
from simgrid import Mailbox, this_actor, SimgridError, Engine, Host # Host might not be needed here
import random # If you keep some simulation logic here

class ProcessingActorCPU: # Renamed from ProcessingActor in your main.py import
    def __init__(self, name: str, my_mailbox_name: str, 
                 dispatcher_mailbox_name: str, database_mailbox_name: str, alert_mailbox_name: str,
                 zone_id: str, # zone_id will now come from the task, not init
                 od_accelerator_mb_name: str, fr_accelerator_mb_name: str):
        """
        name: Name of this CPU processing actor.
        my_mailbox_name: This actor's own mailbox name (to receive tasks from dispatcher, and replies).
        dispatcher_mailbox_name: Mailbox of the DispatcherActor (to send "ready" messages).
        database_mailbox_name: Mailbox of the DatabaseActor.
        alert_mailbox_name: Mailbox of the AlertActor.
        od_accelerator_mb_name: Mailbox of its dedicated OD accelerator.
        fr_accelerator_mb_name: Mailbox of its dedicated FR accelerator.
        """
        self.name = name
        self.my_mailbox_name = my_mailbox_name
        self.my_mailbox = Mailbox.by_name(my_mailbox_name) # Own mailbox
        
        self.dispatcher_mailbox = Mailbox.by_name(dispatcher_mailbox_name)
        self.database_mailbox = Mailbox.by_name(database_mailbox_name)
        self.alert_mailbox = Mailbox.by_name(alert_mailbox_name)
        
        self.od_accelerator_mailbox = Mailbox.by_name(od_accelerator_mb_name)
        self.fr_accelerator_mailbox = Mailbox.by_name(fr_accelerator_mb_name)
        
        # Costs for this CPU part (orchestration, simple logic)
        self.cpu_orchestration_cost = 1e7 # 10 MFlops, e.g.
        self.db_query_flops = 200e6 # From previous estimate
        self.alert_setup_flops = 2e6 # Example
        self.control_message_size = 100 # Bytes for "ready" message

        # Data sizes for communication with accelerators
        # These are just estimates for the metadata/command part, actual data is separate.
        # The visual data part's size will be original_frame_size or derived face_region_size.
        self.task_to_accel_metadata_size = 512 # bytes for task message structure
        self.face_region_data_size_estimate = 50 * 1024 # 50KB example for a cropped face sent to FR

    def _signal_ready_to_dispatcher(self):
        ready_message = {
            "type": "worker_ready",
            "worker_mailbox": self.my_mailbox_name,
            "worker_name": self.name
        }
        this_actor.info(f"({self.name}) Signaling READY to dispatcher.")
        self.dispatcher_mailbox.put(ready_message, self.control_message_size)

    def __call__(self):
        this_actor.info(f"({self.name}) CPU part started. Listening on '{self.my_mailbox_name}'.")
        self._signal_ready_to_dispatcher()

        while True:
            current_task_payload = None # To store the task from dispatcher
            try:
                # 1. Get task from Dispatcher
                current_task_payload = self.my_mailbox.get()
                if not isinstance(current_task_payload, dict) or current_task_payload.get("type") != "frame_task":
                    this_actor.warning(f"({self.name}) Received non-task message or malformed task: {current_task_payload}")
                    self._signal_ready_to_dispatcher() # Become ready again
                    continue

                this_actor.execute(self.cpu_orchestration_cost) # Cost for receiving and parsing task
                
                frame_content_sim = current_task_payload.get("data")
                camera_info = current_task_payload.get("camera_info", {})
                zone_id = camera_info.get("zone", "unknown_zone") # Get zone_id from task
                original_frame_size = current_task_payload.get("original_frame_size")

                this_actor.info(f"({self.name}) Received task: '{frame_content_sim}' from cam '{camera_info.get('id')}' in Z:{zone_id}.")

                # 2. Offload Object Detection
                od_task_msg = {
                    "type": "od_task",
                    "frame_payload": current_task_payload, # Pass along original task for context
                    "original_frame_size": original_frame_size,
                    "reply_to_mailbox": self.my_mailbox_name
                }
                this_actor.info(f"({self.name}) Offloading OD task for frame size {original_frame_size} to OD Accelerator.")
                # Network cost is for sending the frame data to accelerator
                self.od_accelerator_mailbox.put(od_task_msg, original_frame_size) 
                
                # Wait for OD result (blocking get on own mailbox)
                od_response = self.my_mailbox.get()
                if not isinstance(od_response, dict) or od_response.get("type") != "od_result":
                    this_actor.error(f"({self.name}) Expected OD result, got: {od_response}. Aborting task.")
                    self._signal_ready_to_dispatcher()
                    continue
                
                this_actor.execute(self.cpu_orchestration_cost) # Cost for processing OD result
                od_result_data = od_response.get("result", {"person_detected": False})
                this_actor.info(f"({self.name}) Got OD result: Person detected = {od_result_data.get('person_detected')}")

                if od_result_data.get("person_detected"):
                    person_coordinates = od_result_data.get("coordinates")
                    
                    # 3. Offload Facial Recognition
                    fr_task_msg = {
                        "type": "fr_task",
                        "frame_payload_info": current_task_payload, # Pass original task info
                        "person_coordinates": person_coordinates,
                        "face_region_size": self.face_region_data_size_estimate, # Estimated size of data for FR
                        "reply_to_mailbox": self.my_mailbox_name
                    }
                    this_actor.info(f"({self.name}) Offloading FR task (face region size {self.face_region_data_size_estimate}) to FR Accelerator.")
                    # Network cost for sending face region data
                    self.fr_accelerator_mailbox.put(fr_task_msg, self.face_region_data_size_estimate)

                    # Wait for FR result
                    fr_response = self.my_mailbox.get()
                    if not isinstance(fr_response, dict) or fr_response.get("type") != "fr_result":
                        this_actor.error(f"({self.name}) Expected FR result, got: {fr_response}. Aborting FR part.")
                        # Decide if to alert as unknown or just stop this task processing
                        self._signal_ready_to_dispatcher()
                        continue
                        
                    this_actor.execute(self.cpu_orchestration_cost) # Cost for processing FR result
                    face_id = fr_response.get("face_id", "unknown_face")
                    this_actor.info(f"({self.name}) Got FR result: Face ID = {face_id}")

                    if face_id != "unknown_face": # Or other "not recognized" markers
                        # 4. Query Database
                        db_query_payload = {
                            "type": "auth_query",
                            "face_id": face_id,
                            "zone_id": zone_id, # Use zone_id from the task
                            "reply_to_mailbox": self.my_mailbox_name
                        }
                        this_actor.info(f"({self.name}) Querying DB for {face_id} in {zone_id}")
                        self.database_mailbox.put(db_query_payload, 1024) # Small query size

                        # Wait for DB Response
                        db_auth_response = self.my_mailbox.get()
                        if not isinstance(db_auth_response, dict) or db_auth_response.get("type") != "auth_result":
                             this_actor.error(f"({self.name}) Expected DB auth result, got: {db_auth_response}")
                             self._signal_ready_to_dispatcher()
                             continue
                        
                        this_actor.execute(self.cpu_orchestration_cost) # Cost for processing DB response
                        auth_status = db_auth_response.get("status", "Error")
                        this_actor.info(f"({self.name}) DB Auth for {face_id} in {zone_id}: {auth_status}")

                        if auth_status == "Unauthorized":
                            self.send_alert(current_task_payload, face_id, zone_id, "Unauthorized access")
                    else: # Face was unknown from FR step
                        self.send_alert(current_task_payload, face_id, zone_id, "Unknown face detected")
                else: # No person detected by OD
                    this_actor.info(f"({self.name}) No person detected by OD. Task complete.")

                # 5. Signal Ready to Dispatcher
                self._signal_ready_to_dispatcher()

            except SimgridError as e:
                this_actor.error(f"({self.name}) SimgridError in main loop: {e}. Signaling ready.")
                try:
                    self._signal_ready_to_dispatcher() # Attempt to become ready again
                except SimgridError as sig_e:
                     this_actor.error(f"({self.name}) Failed to signal ready after error: {sig_e}")
                # break # Consider if actor should stop on error or try to continue
            except Exception as e_gen:
                this_actor.error(f"({self.name}) GENERIC ERROR in main loop: {e_gen}. Signaling ready.")
                try:
                    self._signal_ready_to_dispatcher()
                except SimgridError as sig_e:
                     this_actor.error(f"({self.name}) Failed to signal ready after generic error: {sig_e}")
                # break


        this_actor.info(f"({self.name}) CPU part stopping.")

    def send_alert(self, original_task_payload, face_id, zone_id, reason):
        camera_id = original_task_payload.get("camera_info", {}).get("id", "unknown_cam")
        alert_data = {
            "type": "alert",
            "timestamp": Engine.clock,
            "zone_id": zone_id,
            "camera_id": camera_id,
            "face_id": face_id,
            "reason": reason
        }
        this_actor.warning(f"({self.name}) SENDING ALERT: {alert_data}")
        try:
            this_actor.execute(self.alert_setup_flops)
            self.alert_mailbox.put(alert_data, 2048) # Example alert size
        except SimgridError as e:
            this_actor.error(f"({self.name}) Failed to send alert: {e}")