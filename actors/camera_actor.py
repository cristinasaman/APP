# camera actor
# - each frame (based on the capture interval) is sent to the processing actor's mailbox 

# TODO: 
#   - determine the frame size for high resolution images and the capture interval
#   - update? the code in main.py for camera actor 

from simgrid import Mailbox, this_actor, SimgridError, Engine

class CameraActor:
    def __init__(self, camera: str, processing_mailbox_name: str, frame_size: int, capture_interval: float):
        """
        camera: Name of the camera actor.
        processing_mailbox: Mailbox name of the target ProcessingActor.
        frame_size: Size of the frame data in bytes.
        capture_interval: Time interval between frame captures in seconds.
        """
        
        self.camera = camera
        self.processing_mailbox_name = processing_mailbox_name
        self.frame_size = frame_size
        self.capture_interval = capture_interval
        
        try:
            self.processing_mailbox = Mailbox.by_name(self.processing_mailbox_name)
        except SimgridError as e:
            this_actor.error(f"Mailbox {self.processing_mailbox_name} not found for camera {self.camera}.")
            raise e
            
    
    def __call__(self):
        this_actor.info(f"Started. Sending frames ({self.frame_size} bytes every {self.capture_interval}s) to {self.processing_mailbox_name}")     
        
        frame_count = 0
        while True:
            try:
                this_actor.sleep_for(self.capture_interval)
                
                frame_count += 1
                payload = f"Frame_{frame_count}_from_{self.camera}_at_{Engine.clock:.3f}"
                this_actor.info(f"Captured '{payload}'. Sending...")        
                self.processing_mailbox.put(payload, self.frame_size)
            
            except SimgridError as e:
                this_actor.error(f"Error while sending frame: {e}")
                break
            
        this_actor.info("Stopping camera actor.")              