# processing actor
# - gets a frame from the camera and applies object detection and facial recognition (if a person is detected)
# - if a person is detected, it queries the database and sends an alert if the person is unauthorized
# TODO:
# - check the logic of the code/ the variables used
# - implment the rest of the functions
# - see how to assign a zone to the processing actor for the database query

from simgrid import Mailbox, this_actor, SimgridError, Engine

class ProcessingActor:
    def __init__(self, processing_node:str, camera: str, database_mailbox_name: str, alert_mailbox_name: str, frame_size: int):
        """
        processing_node: Name of the processing node.
        camera: Name of the camera actor.
        database_mailbox_name: Mailbox name of the DatabaseActor.
        alert_mailbox_name: Mailbox name of the AlertActor.
        frame_size: Size of the frame data in bytes.
        """
        
        self.processing_node = processing_node
        self.mailbox = Mailbox.by_name(processing_node)
        self.camera = camera
        self.database_mailbox_name = database_mailbox_name
        self.alert_mailbox_name = alert_mailbox_name
        self.frame_size = frame_size
        
        try:
            self.database_mailbox = Mailbox.by_name(self.database_mailbox_name)
            self.alert_mailbox = Mailbox.by_name(self.alert_mailbox_name)
            
        except SimgridError as e:
            this_actor.error(f"Mailbox {self.database_mailbox_name} or {self.alert_mailbox_name} not found for processing node {self.processing_node}.")
    
    def __call__(self):        
        this_actor.info(f"Started. Waiting for frames from {self.camera} ({self.frame_size} bytes) on {self.mailbox} at {Engine.clock:.3f}")
        
        while True:
            try:
                frame = self.mailbox.get()
            
                this_actor.info(f"Received frame '{frame}' from {self.camera} at {Engine.clock:.3f}") 
                
                #  Parallelize the object detection and facial recognition tasks
                
                person_found = self.run_object_detection(frame)
                if person_found:
                    this_actor.info(f"Person detected in frame '{frame}'. Running facial recognition...")
                    
                    #  Coordinates (like x_min, y_min, x_max, y_max) defining a rectangle around the detected person in the image.
                    face_id = self.run_facial_recognition(frame)
                    if face_id != "Unnauthorized":
                        self.query_database(face_id)
                    else:
                        this_actor.warning("Unauthorized access detected. Sending alert...")
                        self.send_alert(frame, face_id)
            except SimgridError as e:
                this_actor.error(f"Error while processing frame: {e}")
                break  
        this_actor.info("Stopping processing actor.")
            
            
    def run_object_detection(self, frame):
        flops_od = self.calculate_flops_od()
        person_detected = False
        
        try:
            this_actor.execute(flops_od)
            
            person_detected = self.simulate_person_detection() 
            
            if person_detected:
                this_actor.info("OD Result: Person FOUND.")                 
            else:
                this_actor.info("OD Result: No person detected.")
        
        except SimgridError as e:
            this_actor.error(f"Error during object detection: {e}")   
             
            return False
       
        return person_detected 
    
    
    def run_facial_recognition(self, frame):
        flops_fr = self.calculate_flops_fr()
        face_id = "unknown_face"
        
        try:
            this_actor.execute(flops_fr)
            
            face_id = self.simulate_facial_recognition()
            
        except SimgridError as e:
            this_actor.error(f"Error during facial recognition: {e}")        
         
        return face_id    
    
    
    def query_database(self, face_id):
        query_data = f"Query: {face_id}, Zone ID: {self.processing_node}"
        query_size = 1000
        
        try:
            this_actor.info(f"Querying database with Face ID: {face_id} at {Engine.clock:.3f}")
            this_actor.execute(1000)  # Simulate query time
            self.database_mailbox.put(query_data, query_size)
            
            response = self.database_mailbox.get()
            this_actor.info(f"Received response from database: {response} at {Engine.clock:.3f}")
            
        except SimgridError as e:
            this_actor.error(f"Error during database query: {e}")
            return False
    
        return response
    
    
    def send_alert(self, frame, face_id):
        alert_data = f"Alert: {frame}, Face ID: {face_id}"
        alert_size = 2000
        try:
            this_actor.info(f"Sending alert: {alert_data} at {Engine.clock:.3f}")
            this_actor.execute(2000)  # Simulate alert sending time
            self.alert_mailbox.put(alert_data, alert_size)
            
        except SimgridError as e:
            this_actor.error(f"Error during alert sending: {e}")
            return False
        
        return True
    
    def simulate_person_detection(self, frame):
        # Simulate the object detection process
        # In a real scenario, this would involve running a model on the frame data
        
        # results = model(frame)
        # box, confidence, class_id = results[0]
        
        
        return True