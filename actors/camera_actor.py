from simgrid import Mailbox, this_actor, SimgridError, Engine

class CameraActor:
    def __init__(self, camera: str, zone_id: str, dispatcher_mailbox_name: str, frame_size: int, capture_interval: float): # Added max_frames from previous suggestion, let's make sure it's included if used
        """
        camera: Name of the camera actor.
        zone_id: ID of the zone where the camera is located.
        dispatcher_mailbox_name: Mailbox name of the target DispatcherActor.
        frame_size: Size of the frame data in bytes.
        capture_interval: Time interval between frame captures in seconds.
        """
        self.camera = camera
        self.zone_id = zone_id
        self.dispatcher_mailbox_name = dispatcher_mailbox_name
        self.frame_size = frame_size
        self.capture_interval = capture_interval
        # self.max_frames = max_frames # Add this if you use MAX_FRAMES_PER_CAMERA

        try:
            self.dispatcher_mailbox = Mailbox.by_name(self.dispatcher_mailbox_name)
        except SimgridError as e:
            this_actor.error(f"Mailbox {self.dispatcher_mailbox_name} not found for camera {self.camera}.") # Corrected: self.camera
            raise e

    def __call__(self):
        # Corrected log message to use the dispatcher_mailbox_name
        this_actor.info(f"Started. Sending frames ({self.frame_size} bytes every {self.capture_interval}s) to {self.dispatcher_mailbox_name}")

        frame_count = 0
        # Consider adding max_frames if used: while frame_count < self.max_frames:
        while True:
            try:
                this_actor.sleep_for(self.capture_interval)

                frame_count += 1
                payload = {
                    "type": "frame_task", # Good for dispatcher
                    "frame_id": f"Frame_{frame_count}_from_{self.camera}",
                    "timestamp": Engine.clock, # Correct: use Engine.clock
                    "zone_id": self.zone_id,
                    "original_camera": self.camera, # Renamed for clarity
                    "original_frame_size": self.frame_size # Added for dispatcher/processor
                }
                this_actor.info(f"Zone '{self.zone_id}' Camera '{self.camera}' captured frame {frame_count}. Sending...")
                self.dispatcher_mailbox.put(payload, self.frame_size) # self.frame_size is a good estimate for the primary data size

            except SimgridError as e:
                this_actor.error(f"Camera '{self.camera}' error while sending frame: {e}")
                break

        this_actor.info(f"Camera '{self.camera}' stopping.")