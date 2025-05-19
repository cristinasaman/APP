from simgrid import Mailbox, this_actor, Engine
import random

class AcceleratorActorFR:
    def __init__(self, name: str, my_mailbox_name: str):
        """
        name: Name of the actor.    
        my_mailbox_name: Name of the mailbox for this actor.
        """
        
        self.name = name
        self.my_mailbox = Mailbox.by_name(my_mailbox_name)
        self.base_fr_flops_per_face_region = 2e11  
        self.fr_parallelism_factor = 16
        
        self.total_computation_time = 0.0
        self.total_wait_time_for_task = 0.0
        self.total_communication_send_time = 0.0
        
        this_actor.info(f"({self.name}) FR Accelerator ready on mailbox '{my_mailbox_name}'.")

    def __call__(self):
        while True:
            try:
                time_before_get = Engine.clock
                task_message = self.my_mailbox.get()
                self.total_wait_time_for_task += (Engine.clock - time_before_get)


                reply_to_mb_name = task_message.get("reply_to_mailbox")
                face_region_size = task_message.get("face_region_size")
                person_coordinates = task_message.get("face_coordinates")
                frame_info_for_sim = task_message.get("frame_payload_info")

                if not all([reply_to_mb_name, face_region_size is not None, person_coordinates]):
                    this_actor.warning(f"({self.name}) Received incomplete FR task: {task_message}")
                    continue

                this_actor.info(f"({self.name}) Received FR task for frame from '{frame_info_for_sim.get('camera_info', {}).get('id')}', face region size {face_region_size}. Replying to '{reply_to_mb_name}'.")

                fr_flops = self._calculate_flops_fr(face_region_size)
                
                time_before_exec = Engine.clock
                this_actor.execute(fr_flops)
                computation_duration = Engine.clock - time_before_exec
                self.total_computation_time += computation_duration

                face_id = self._simulate_fr_result(frame_info_for_sim, person_coordinates)

                response_payload = {
                    "type": "fr_result",
                    "original_task": task_message,
                    "face_id": face_id
                }
                result_message_size_bytes = 512

                try:
                    reply_mailbox = Mailbox.by_name(reply_to_mb_name)
                    time_before_put = Engine.clock
                    reply_mailbox.put(response_payload, result_message_size_bytes)
                    self.total_communication_send_time += (Engine.clock - time_before_put)
                except Exception as e:
                    this_actor.error(f"({self.name}) Failed to send FR result to '{reply_to_mb_name}': {e}")

            except Exception as e:
                this_actor.error(f"({self.name}) FR Accelerator error: {e}")
                break

        this_actor.info(f"({self.name}) FR Accelerator stopping.")
 
    def _calculate_flops_fr(self, face_region_size_bytes):
        cost = (self.base_fr_flops_per_face_region / (100 * 1024)) * face_region_size_bytes
        
        return cost / self.fr_parallelism_factor

    def _simulate_fr_result(self, frame_data_info, person_coordinates):
        if not person_coordinates:
            return "unknown_face"
        
        return random.choice(["employee_123", "employee_456", "visitor_789", "unknown_face"])
        