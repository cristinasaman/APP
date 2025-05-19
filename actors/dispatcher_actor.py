from simgrid import Mailbox, this_actor, Engine
import collections
import openpyxl
import os

class DispatcherActor:
    def __init__(self, mailbox_name: str):
        """
        mailbox_name: Name of the mailbox for this DispatcherActor.
        mailbox: The mailbox object for this actor.
        task_queue: Queue for incoming tasks.
        available_workers_queue: Queue for available workers.
        dispatch_cost: Cost of dispatching a task to a worker. (in MFlops)
        total_wait_time_on_get: Total wait time for getting tasks.
        total_dispatch_computation_time: Total computation time for dispatching tasks.
        """
        
        self.mailbox_name = mailbox_name
        self.mailbox = Mailbox.by_name(mailbox_name)
        self.task_queue = collections.deque()
        self.available_workers_queue = collections.deque()
        self.dispatch_cost = 1e6 
        self.total_wait_time_on_get = 0.0
        self.total_dispatch_computation_time = 0.0
        
        this_actor.info(f"Dispatcher initialized with mailbox '{self.mailbox_name}'.")

    def __call__(self):
        this_actor.info(f"Started. Listening for tasks and workers on '{self.mailbox_name}'.")
        
        while True:
            try:
                message = self.mailbox.get()
                time_before_execute = Engine.clock
                this_actor.execute(self.dispatch_cost)
                self.total_dispatch_computation_time += (Engine.clock - time_before_execute)

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
        
        # self._write_metrics_to_excel()
            
        this_actor.info(f"Dispatcher stopping.")

    def _try_dispatch_tasks(self):
        while self.task_queue and self.available_workers_queue:
            task_to_dispatch = self.task_queue.popleft()
            worker_mailbox_name = self.available_workers_queue.popleft()

            try:
                worker_mailbox = Mailbox.by_name(worker_mailbox_name)
                message_size_to_worker = 1024 
                worker_mailbox.put(task_to_dispatch, message_size_to_worker)
                
                time_before_execute = Engine.clock
                this_actor.execute(self.dispatch_cost)
                self.total_dispatch_computation_time += (Engine.clock - time_before_execute)
                
                cam_info = task_to_dispatch.get('camera_info', {})
                cam_id = cam_info.get('id', 'UnknownCam')
                
                this_actor.info(f"Dispatched task (from cam: {cam_id}) to worker '{worker_mailbox_name}'. Tasks left: {len(self.task_queue)}. Workers avail: {len(self.available_workers_queue)}")
                
            except Exception as e:
                this_actor.error(f"Failed to dispatch task to worker '{worker_mailbox_name}': {e}. Re-queuing worker and task.")
                self.available_workers_queue.append(worker_mailbox_name)
                self.task_queue.appendleft(task_to_dispatch)
                break
    
    def _write_metrics_to_excel(self):
        filename = "simulation_metrics.xlsx"
        sheet_name = "DispatcherMetrics"

        if not os.path.exists(filename):
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = sheet_name
            ws.append(["Actor", "Computation Time (s)", "Communication Wait Time (s)"])
        else:
            wb = openpyxl.load_workbook(filename)
            if sheet_name not in wb.sheetnames:
                ws = wb.create_sheet(title=sheet_name)
                ws.append(["Actor", "Computation Time (s)", "Communication Wait Time (s)"])
            else:
                ws = wb[sheet_name]

        ws.append([
            f"{this_actor.name}", 
            round(self.total_wait_time_on_get, 6), 
            round(self.total_dispatch_computation_time, 6)
        ])

        wb.save(filename)        