# Conceptual Pipeline Recap

1. Capture: Camera N captures a frame.

2. Send: Frame sent over the network to a processing unit.

3. Detect: Object Detection (OD) runs on the frame.
  - Parallelism: Task (multiple cameras) & potentially Data (within high-res frame).

4. Check: If 'person' detected:
  - Recognize: Facial Recognition (FR) runs on the face region.
  - Query: Send Face ID + Camera N's Zone ID to Database Server.
  - Verify Access: Database Server checks if Face ID is authorized for Zone ID (Access Rules Applied Here).
  - Receive Result: Processing unit gets Authorized/Unauthorized response.
  
5. Alert: If unauthorized, send an alert to the Central Alert Server/Monitoring Station.