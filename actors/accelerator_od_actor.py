from simgrid import Mailbox, this_actor, Engine
import random

class AcceleratorActorOD:
    def __init__(self, name: str, my_mailbox_name: str):
        """
        name: Name of the actor.
        my_mailbox_name: Name of the mailbox for this actor.
        """
        
        self.name = name
        self.my_mailbox = Mailbox.by_name(my_mailbox_name)
        self.base_od_flops_per_mb = 1e12 
        self.od_parallelism_factor = 8
        
        self.total_computation_time = 0.0
        self.total_wait_time_for_task = 0.0
        self.total_communication_send_time = 0.0
        
        this_actor.info(f"({self.name}) OD Accelerator ready on mailbox '{my_mailbox_name}'.")

    def __call__(self):
        while True:
            try:
                time_before_get = Engine.clock
                task_message = self.my_mailbox.get()
                self.total_wait_time_for_task += (Engine.clock - time_before_get)

                reply_to_mb_name = task_message.get("reply_to_mailbox")
                original_frame_size = task_message.get("original_frame_size")
                frame_info_for_sim = task_message.get("frame_payload")

                if not all([reply_to_mb_name, original_frame_size is not None]):
                    this_actor.warning(f"({self.name}) Received incomplete OD task: {task_message}")
                    continue

                this_actor.info(f"({self.name}) Received OD task for frame from '{frame_info_for_sim.get('camera_info', {}).get('id')}', size {original_frame_size}. Replying to '{reply_to_mb_name}'.")

                od_flops = self._calculate_flops_od(original_frame_size)
                time_before_exec = Engine.clock
                this_actor.execute(od_flops)
                computation_duration = Engine.clock - time_before_exec
                self.total_computation_time += computation_duration

                od_result_data = self._simulate_od_result(frame_info_for_sim)

                response_payload = {
                    "type": "od_result",
                    "original_task": task_message,
                    "result": od_result_data
                }

                try:
                    reply_mailbox = Mailbox.by_name(reply_to_mb_name)
                    reply_mailbox.put(response_payload, 1024)
                except Exception as e:
                    this_actor.error(f"({self.name}) Failed to send OD result to '{reply_to_mb_name}': {e}")

            except Exception as e:
                this_actor.error(f"({self.name}) OD Accelerator error: {e}")
                break

        this_actor.info(f"({self.name}) OD Accelerator stopping.")
        
    def _calculate_flops_od(self, frame_size_bytes):
        cost = (self.base_od_flops_per_mb / (1024 * 1024)) * frame_size_bytes
        
        return cost / self.od_parallelism_factor

    def _simulate_od_result(self, frame_data_info):
        person_detected = random.choice([True, False, True])
        coordinates = None
        
        if person_detected:
            coordinates = [random.randint(0, 100), random.randint(0, 100),
                           random.randint(100, 200), random.randint(100, 200)]
            
        return {"person_detected": person_detected, "coordinates": coordinates}        