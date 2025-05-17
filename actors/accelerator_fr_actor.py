from simgrid import Mailbox, this_actor, SimgridError, Engine

class AcceleratorActorFR:
    def __init__(self, name: str, my_mailbox_name: str):
        self.name = name
        self.my_mailbox = Mailbox.by_name(my_mailbox_name)
        # FR-specific parameters
        self.base_fr_flops_per_face_region = 2e11 # Example: 0.2 TFLOPs for a typical face region
        self.fr_parallelism_factor = 16
        this_actor.info(f"({self.name}) FR Accelerator ready on mailbox '{my_mailbox_name}'.")

    def _calculate_flops_fr(self, face_region_size_bytes): # FR cost might depend on region size
        cost = (self.base_fr_flops_per_face_region / (100*1024)) * face_region_size_bytes # Normalize to 100KB region
        return cost / self.fr_parallelism_factor

    def _simulate_fr_result(self, frame_data_info, person_coordinates):
        # This logic was previously in ProcessingActor.simulate_facial_recognition
        # For simplicity, using a basic random version here.
        import random
        if not person_coordinates: return "unknown_face"
        # Your detailed simulation logic from ProcessingActor.simulate_facial_recognition can be moved/adapted here
        return random.choice(["employee_123", "employee_456", "visitor_789", "unknown_face"])

    def __call__(self):
        while True:
            try:
                # Task message should include:
                # { "type": "fr_task", "frame_payload_info": ..., "person_coordinates": ..., "face_region_size": ..., "reply_to_mailbox": ... }
                task_message = self.my_mailbox.get()

                reply_to_mb_name = task_message.get("reply_to_mailbox")
                face_region_size = task_message.get("face_region_size") # Estimated size of face data sent
                person_coordinates = task_message.get("person_coordinates")
                frame_info_for_sim = task_message.get("frame_payload_info")

                if not all([reply_to_mb_name, face_region_size is not None, person_coordinates]):
                    this_actor.warning(f"({self.name}) Received incomplete FR task: {task_message}")
                    continue
                
                this_actor.info(f"({self.name}) Received FR task for frame from '{frame_info_for_sim.get('camera_info',{}).get('id')}', face region size {face_region_size}. Replying to '{reply_to_mb_name}'.")

                # 1. Simulate FR computation
                fr_flops = self._calculate_flops_fr(face_region_size)
                this_actor.execute(fr_flops)

                # 2. Simulate FR result
                face_id = self._simulate_fr_result(frame_info_for_sim, person_coordinates)

                # 3. Send result back
                response_payload = {
                    "type": "fr_result",
                    "original_task": task_message,
                    "face_id": face_id
                }
                reply_mailbox = Mailbox.by_name(reply_to_mb_name)
                reply_mailbox.put(response_payload, 512) # Small size for result message
                this_actor.info(f"({self.name}) Sent FR result ('{face_id}') back to '{reply_to_mb_name}'.")

            except SimgridError as e:
                this_actor.error(f"({self.name}) FR Accelerator error: {e}")
                break
        this_actor.info(f"({self.name}) FR Accelerator stopping.")