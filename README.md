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


# Project Details

1. Distributed Network
  -  You are modeling a system with components (cameras, processing nodes, servers) that are distinct and communicate over a network (represented by links and routes in SimGrid). This inherently makes it a distributed system.

2. Multiple Instruction, Multiple Data
  - Multiple Instruction Streams: Each ProcessingActor instance runs independently, executing its own sequence of instructions based on the code and the data it receives. You have multiple, independent threads of execution (instruction streams).
  - Multiple Data Streams: Each camera provides a distinct, independent stream of data (the video frames).

  Therefore, multiple processing units are executing potentially different instructions on different data streams concurrently, which is the definition of MIMD.  

(Side Note on Data Parallelism: If, within the Object Detection step on a single high-resolution frame, you were simulating splitting the frame and using something like GPU acceleration where the same detection kernel runs on all parts of the split frame simultaneously, that specific sub-step might leverage SIMD principles. However, the overall system architecture coordinating these independent processing pipelines across the network remains firmly MIMD.)  

3. Communication 
  - message passing for distributed memories?

4. Network
  - central routing

5. GPU acceleration  

6. Parallelism

7. Metrici?