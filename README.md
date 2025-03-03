# APP Project Details

## Steps for the implementation:
  1. Chooseing a suitable object detection algorithm that supports parallelism. (see MPI?)
  2. Leveraging parallel hardware like multiple GPUs or distributed computing.
  3. Using SimGrid to simulate the distributed execution and test scalability.
     
----

## TOP500 for additional ideas:
  - GPU Acceleration: many top supercomputers utilize GPU acceleration to enhance computational performance, a strategy that can be applied to the object detection application.
  - Performance Optimization: understanding the architectures of these supercomputers can provide ideas on optimizing data flow and processing efficiency in the system.
  - Scalability Considerations: insights into how these systems manage large-scale computations can inform the scalability aspects of the application.

----

## Small-Scale Implementation Plan
- the structure of the basic but functional prototype with the following essential components:

  1. Object Detection Implementation (Software)
  - use a pre-trained model (e.g., YOLOv5 or OpenCV Haar cascades) to avoid training complexity.
  - process images/video frames in parallel instead of handling a full video stream in real time.
  - use Python & OpenCV/TensorFlow/PyTorch for simplicity.

  2. Parallelization on a Single Machine (Hardware)
  - if you have a GPU, leverage CUDA for parallel processing.
  - if no GPU is available, you can still use multiple CPU threads to simulate parallelism.
  - example: process multiple images in parallel using Python’s multiprocessing or PyTorch’s DataParallel.

  3. SimGrid Simulation (Performance Testing)
  - model a simple multi-GPU architecture virtually in SimGrid.
  - simulate different workloads (e.g., 1 vs. 2 vs. 4 GPUs) to evaluate parallel efficiency.
  - analyze execution time and resource utilization.
