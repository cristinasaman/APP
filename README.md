# Proposed Application Title:
Parallel Real-Time Object Detection for Smart Camera Surveillance

## Application Overview:
This application performs real-time object detection across multiple surveillance camera feeds using a parallel architecture. The system is designed to process video streams from several cameras concurrently, identify objects of interest (e.g., people, vehicles), and raise alerts based on predefined rules (e.g., unauthorized access, crowding, unattended bags).

## Why Parallelism Is Essential:
1. Multiple Video Feeds:
  Each camera stream is processed independently, which is a perfect case for task parallelism.

2. Frame Processing Pipeline:
  For each video stream, object detection involves several compute-heavy stages:

  - Frame acquisition

  - Preprocessing (resizing, denoising, etc.)

  - Inference using a trained model (e.g., YOLO, SSD)

  - Postprocessing (bounding boxes, tracking)

  These stages can be pipelined and parallelized internally as well, e.g., using multithreading or GPU acceleration.

3. Alert Management and Logging:
  Once objects are detected, the system must also log events and possibly notify a central controller. This component can also be parallelized—e.g., using separate threads or processes to handle each type of event.

## Hardware Parallelism:
  - Multiple cores/threads for processing separate streams.

  - GPU acceleration for deep learning inference.

  - Optional use of edge devices vs. centralized servers (hybrid architecture).

## Software Parallelism:
  - Use of threads or processes for stream handling (e.g., OpenMP, pthreads).

  - Use of MPI (Message Passing Interface) to model distributed processing across nodes.

  - Internal concurrency in the detection pipeline (e.g., using concurrent queues for pipelining).

## 🔐 Scenario Description: Restricted Area Surveillance in a Data Center
In this scenario, we design and simulate a real-time object detection system used to monitor access to high-security server rooms in a corporate data center. These rooms contain critical IT infrastructure and are only accessible to a limited number of authorized personnel.

The surveillance system adds an intelligent, automated layer to existing badge-based access control. It uses cameras installed at the entry points and within the room to detect the presence of individuals and verify that access rules are being followed.

## Key Objectives:
  - Ensure that only authorized personnel are physically present in the room.
  
  - Detect and alert on unauthorized access, after-hours entry, or tailgating (more than one person entering on a single ID).
  
  - Monitor for potential safety concerns, such as a person being unresponsive for an extended period inside the room.

## How the System Works:
1. Person Entry Detected: A camera at the entrance begins recording when the door opens.

2. Human Detection: The system performs object detection to identify the presence of people in the camera frame.

3. Identity Check:

The system cross-checks the detected person with the badge or facial recognition data.

4. Rule Evaluation:

  - If the person is authorized → Log entry.
  
  - If unknown → Raise alert.
  
  - If more than one person is detected and only one badge was used → Raise alert.
  
  - If person is detected during restricted hours → Raise alert.
  
  - If a person remains inside with no movement beyond a certain time → Raise safety alert.

## System Architecture:
  - Each server room is monitored by an independent processing unit responsible for handling its camera feed and rule evaluation.
  
  - These units operate in parallel, allowing the system to scale across multiple rooms or zones.
  
  - A central node (e.g., security server) receives alerts and logs from each room and provides a unified interface for security personnel.

## Simulation in SimGrid:
This architecture can be modeled in SimGrid by:
  
  - Defining each room as a processing node, handling camera input and detection logic.
  
  - Modeling the central logging/alerting system as a separate node.
  
  - Simulating communication between nodes using message passing.
  
  - Introducing variable workloads (e.g., more entries during working hours) and network latency to test system behavior and scalability.
  
  - This scenario is ideal for parallel processing because:
  
  - Multiple cameras/rooms work independently (task-level parallelism).
  
  - Each detection task involves multiple parallel software stages (data-level parallelism).
  
  - Communication and alerting are decoupled, allowing asynchronous operation.
