from simgrid import Mailbox, this_actor, Engine

class AcceleratorActorOD:
    def __init__(self, name: str, my_mailbox_name: str):
        self.name = name
        self.my_mailbox = Mailbox.by_name(my_mailbox_name)
        # OD-specific parameters could be initialized here if needed
        # For example, how to calculate FLOPs based on frame_size
        self.base_od_flops_per_mb = 1e12 # Example: 1 TFLOP per MB of frame data (adjust)
        self.od_parallelism_factor = 8 # How much data parallelism speeds it up

        this_actor.info(f"({self.name}) OD Accelerator ready on mailbox '{my_mailbox_name}'.")

    def _calculate_flops_od(self, frame_size_bytes):
        # Simplified cost calculation based on frame size
        # This logic was previously in ProcessingActor
        cost = (self.base_od_flops_per_mb / (1024*1024)) * frame_size_bytes
        return cost / self.od_parallelism_factor # Account for internal data parallelism

    def _simulate_od_result(self, frame_data_info):
        # This logic was previously in ProcessingActor.simulate_person_detection
        # For simplicity, using a basic random version here.
        # You can move your more detailed simulation here.
        import random
        person_detected = random.choice([True, False, True]) # Higher chance of detection
        coordinates = None
        if person_detected:
            coordinates = [random.randint(0,100), random.randint(0,100), 
                           random.randint(100,200), random.randint(100,200)]
        return {"person_detected": person_detected, "coordinates": coordinates}

    def __call__(self):
        while True:
            try:
                # Task message should include:
                # { "type": "od_task", "frame_payload": ..., "original_frame_size": ..., "reply_to_mailbox": ... }
                task_message = self.my_mailbox.get()
                
                reply_to_mb_name = task_message.get("reply_to_mailbox")
                original_frame_size = task_message.get("original_frame_size")
                frame_info_for_sim = task_message.get("frame_payload") # For logging or more complex simulation

                if not all([reply_to_mb_name, original_frame_size is not None]):
                    this_actor.warning(f"({self.name}) Received incomplete OD task: {task_message}")
                    continue

                this_actor.info(f"({self.name}) Received OD task for frame from '{frame_info_for_sim.get('camera_info',{}).get('id')}', size {original_frame_size}. Replying to '{reply_to_mb_name}'.")

                # 1. Simulate OD computation
                od_flops = self._calculate_flops_od(original_frame_size)
                this_actor.execute(od_flops)

                # 2. Simulate OD result
                od_result_data = self._simulate_od_result(frame_info_for_sim)
                
                # 3. Send result back
                response_payload = {
                    "type": "od_result",
                    "original_task": task_message, # Echo back original task info if needed
                    "result": od_result_data
                }
                reply_mailbox = Mailbox.by_name(reply_to_mb_name)
                reply_mailbox.put(response_payload, 1024) # Small size for result message
                this_actor.info(f"({self.name}) Sent OD result back to '{reply_to_mb_name}'.")

            except Exception as e:
                this_actor.error(f"({self.name}) OD Accelerator error: {e}")
                break # Exit loop on SimgridError
        this_actor.info(f"({self.name}) OD Accelerator stopping.")