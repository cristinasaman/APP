# dispatcher_actor.py (or add to your main actor file)
from simgrid import Actor, Engine, Host, Mailbox, this_actor, SimgridError
import collections # For deque

class DispatcherActor:
    def __init__(self, mailbox_name: str):
        self.mailbox_name = mailbox_name
        self.mailbox = Mailbox.by_name(mailbox_name)
        
        # Queue for incoming frames/tasks from cameras
        # Each item could be the payload dictionary directly from CameraActor
        self.task_queue = collections.deque()
        
        # Queue for available worker (ProcessingActor) mailbox names
        self.available_workers_queue = collections.deque()
        
        self.dispatch_cost = 1e6 # Small flop cost for dispatch logic, e.g., 1 Mflop

    def __call__(self):
        this_actor.info(f"Started. Listening for tasks and workers on '{self.mailbox_name}'.")

        while True:
            try:
                # Wait for any message (either a frame task or a worker ready notification)
                message = self.mailbox.get() 
                this_actor.execute(self.dispatch_cost) # Simulate cost of receiving and initial processing

                if not isinstance(message, dict) or "type" not in message:
                    this_actor.warning(f"Received malformed message: {message}")
                    continue

                msg_type = message["type"]

                if msg_type == "frame_task":
                    self.task_queue.append(message) # Add task (which is the message dict) to queue
                    this_actor.info(f"Received new frame task from '{message.get('camera_info', {}).get('id', 'UnknownCam')}' for zone '{message.get('camera_info', {}).get('zone', 'UnknownZone')}'. Tasks queued: {len(self.task_queue)}.")
                
                elif msg_type == "worker_ready":
                    worker_mb_name = message.get("worker_mailbox")
                    if worker_mb_name:
                        self.available_workers_queue.append(worker_mb_name)
                        this_actor.info(f"Worker '{worker_mb_name}' reported ready. Available workers: {len(self.available_workers_queue)}.")
                    else:
                        this_actor.warning("Received worker_ready message without mailbox name.")
                
                else:
                    this_actor.warning(f"Received unknown message type: {msg_type}")

                # Attempt to dispatch tasks
                self._try_dispatch_tasks()

            except SimgridError as e:
                this_actor.error(f"Error in main loop: {e}")
                break # Exit on critical error
        
        this_actor.info("Stopping.")

    def _try_dispatch_tasks(self):
        """Attempts to assign tasks from queue to available workers."""
        while self.task_queue and self.available_workers_queue:
            task_to_dispatch = self.task_queue.popleft()
            worker_mailbox_name = self.available_workers_queue.popleft()

            try:
                worker_mailbox = Mailbox.by_name(worker_mailbox_name)
                # The 'task_to_dispatch' is the dictionary received from the camera
                # The frame_size for network cost was handled when camera sent to dispatcher.
                # Now dispatcher sends to worker. The size here should be task_to_dispatch's actual size.
                # SimGrid Python bindings often pickle dicts, so size is estimated.
                # Let's assume the frame_size in the task_to_dispatch refers to the visual data size
                # for the worker's processing, not necessarily the message size here.
                # We'll re-use the original frame_size for consistency, assuming metadata is small.
                
                frame_data_size = task_to_dispatch.get("original_frame_size", 1024) # Default if not present
                worker_mailbox.put(task_to_dispatch, frame_data_size) # Sending the whole task dict
                
                this_actor.execute(self.dispatch_cost) # Simulate cost of dispatching
                this_actor.info(f"Dispatched task (from cam: {task_to_dispatch.get('camera_info', {}).get('id')}) to worker '{worker_mailbox_name}'. Tasks left: {len(self.task_queue)}. Workers avail: {len(self.available_workers_queue)}")
            except SimgridError as e:
                this_actor.error(f"Failed to dispatch task to worker '{worker_mailbox_name}': {e}. Re-queuing worker (if possible) and task.")
                # Simplistic error handling: re-add worker and task if dispatch fails
                self.available_workers_queue.append(worker_mailbox_name) # Re-add worker
                self.task_queue.appendleft(task_to_dispatch) # Re-add task to front
                break # Stop trying to dispatch this round to avoid potential loops on same error