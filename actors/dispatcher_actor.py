# dispatcher_actor.py (or add to your main actor file)
from simgrid import Actor, Engine, Host, Mailbox, this_actor # Engine not strictly needed here
import collections # For deque

class DispatcherActor:
    def __init__(self, mailbox_name: str):
        self.mailbox_name = mailbox_name
        self.mailbox = Mailbox.by_name(mailbox_name)
        self.task_queue = collections.deque()
        self.available_workers_queue = collections.deque()
        self.dispatch_cost = 1e6 
        
        this_actor.info(f"Dispatcher initialized with mailbox '{self.mailbox_name}'.")

    def __call__(self):
        this_actor.info(f"Started. Listening for tasks and workers on '{self.mailbox_name}'.")
        
        while True:
            try:
                message = self.mailbox.get()
                this_actor.execute(self.dispatch_cost)

                if not isinstance(message, dict) or "type" not in message:
                    this_actor.warning(f"Received malformed message: {message}")
                    continue

                msg_type = message["type"]

                if msg_type == "frame_task":
                    self.task_queue.append(message)
                    cam_info = message.get('camera_info', {})
                    cam_id = cam_info.get('id', 'UnknownCam')
                    zone_id = cam_info.get('zone', 'UnknownZone')
                    
                    this_actor.info(f"Received new frame task from '{cam_id}' for zone '{zone_id}'. Tasks queued: {len(self.task_queue)}.")
                elif msg_type == "worker_ready":
                    worker_mb_name = message.get("worker_mailbox")
                    worker_name = message.get("worker_name", "UnknownWorker") 
                    
                    if worker_mb_name:
                        self.available_workers_queue.append(worker_mb_name)
                        this_actor.info(f"Worker '{worker_name}' ({worker_mb_name}) reported ready. Available workers: {len(self.available_workers_queue)}.")
                    else:
                        this_actor.warning("Received worker_ready message without mailbox name.")
                else:
                    this_actor.warning(f"Received unknown message type: {msg_type}")

                self._try_dispatch_tasks()

            except Exception as e:
                this_actor.error(f"Error in main loop: {e}")
                break
        this_actor.info("Stopping.")

    def _try_dispatch_tasks(self):
        while self.task_queue and self.available_workers_queue:
            task_to_dispatch = self.task_queue.popleft()
            worker_mailbox_name = self.available_workers_queue.popleft()

            try:
                worker_mailbox = Mailbox.by_name(worker_mailbox_name)
                
                message_size_to_worker = 1024 
                
                worker_mailbox.put(task_to_dispatch, message_size_to_worker)
                
                this_actor.execute(self.dispatch_cost)
                cam_info = task_to_dispatch.get('camera_info', {})
                cam_id = cam_info.get('id', 'UnknownCam')
                this_actor.info(f"Dispatched task (from cam: {cam_id}) to worker '{worker_mailbox_name}'. Tasks left: {len(self.task_queue)}. Workers avail: {len(self.available_workers_queue)}")
                
            except Exception as e:
                this_actor.error(f"Failed to dispatch task to worker '{worker_mailbox_name}': {e}. Re-queuing worker and task.")
                self.available_workers_queue.append(worker_mailbox_name)
                self.task_queue.appendleft(task_to_dispatch)
                break