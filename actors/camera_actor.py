from simgrid import Mailbox, this_actor, Engine

class CameraActor:
    def __init__(self, camera: str, zone_id: str, dispatcher_mailbox_name: str, frame_size: int, capture_interval: float, max_frames: int):
        """
        camera: Name of the camera actor.
        zone_id: ID of the zone where the camera is located.
        dispatcher_mailbox_name: Mailbox name of the target DispatcherActor.
        frame_size: Size of the frame data in bytes.
        capture_interval: Time interval between frame captures in seconds.
        max_frames: Maximum number of frames to capture (if using MAX_FRAMES_PER_CAMERA).
        """
        
        self.camera = camera
        self.zone_id = zone_id
        self.dispatcher_mailbox_name = dispatcher_mailbox_name
        self.frame_size = frame_size
        self.capture_interval = capture_interval
        self.max_frames = max_frames

        try:
            self.dispatcher_mailbox = Mailbox.by_name(self.dispatcher_mailbox_name)
        except Exception as e:
            this_actor.error(f"Mailbox {self.dispatcher_mailbox_name} not found for camera {self.camera}.") 
            raise e
        
        this_actor.info(f"Camera '{self.camera}' initialized with zone '{self.zone_id}'. Targeting mailbox '{self.dispatcher_mailbox_name}'. Frame size: {self.frame_size} bytes. Capture interval: {self.capture_interval} seconds. Max frames: {self.max_frames}.")

    def __call__(self):
        this_actor.info(f"Camera '{self.camera}' __call__ STARTED.")
        this_actor.info(f"({self.camera} in Zone {self.zone_id}) Started. Target: '{self.dispatcher_mailbox_name}'. Max frames: {self.max_frames if self.max_frames != float('inf') else 'unlimited'}.")
        
        frame_count = 0
        while frame_count < self.max_frames: 
            try:
                this_actor.sleep_for(self.capture_interval)
                
                frame_count += 1
                payload_content = f"Frame_{frame_count}_from_{self.camera}"
                
                payload = {
                    "type": "frame_task",
                    "data": payload_content,
                    "camera_info": { 
                        "id": self.camera,
                        "zone": self.zone_id,
                        "timestamp": Engine.clock 
                    },
                    "original_frame_size": self.frame_size
                }
                
                this_actor.info(f"Zone '{self.zone_id}' Camera '{self.camera}' captured frame {frame_count}/{self.max_frames}. Sending...")
                self.dispatcher_mailbox.put(payload, self.frame_size) 
            
            except Exception as e_gen:
                this_actor.error(f"Camera '{self.camera}' UNEXPECTED error: {type(e_gen).__name__} - {e_gen}")
                break
            
        this_actor.info(f"Camera '{self.camera}' finished sending {frame_count} frames. Stopping.")
