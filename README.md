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

conditii ca aplicatia si arhitectura sa fie paralele
metrici in parte teoretica? - legea Amdahl, 
focus pe paralelizare? justificare de ce e paralelizabila
hardware suporta paralelism - unitati de executie pentru task-uri

definire task-uri care se executa in paralel
definire arhitectura pe care se executa task-uri si aratam exemplu de paralelism? (adica ce folosesc?)

focus pe tip de arhitectura (shared, distributed, )
acceleratori? SIMD 

noduri conectate prin retea -> in interiorul nodului (memorie partajata pe un numar de core-uri + accelarator specific sarcinii lui)
memorie distribuita - nu e limitata 
hardware -> host-uri cu capacitate de procesare
partea de accelare nu se descompune - fiecare accelerator este un host separat - bottleneck-ul se simuleaza 
arhitectura unificata de memorie? -> accelerator legat la core-uri obisnuite prin intermediul unui link (PCIX?)
legaturi - latime de banda, latenta
costuri la echipamente 
link-uri si rute

software:
paradigma - message passing - procese
biblioteci 
procese - actioneaza concurent si comunica intre ele - schimbare data si sincronizare
accelerator pentru actor
cutii postale si cat de mari sunt task-urile pentru actor si proces astfel incat 
partea de calcul trebuie sa domine partea de comunicatie
dimensiune imagine -> cate operatii face actorul pentru calcul - timp de comunicatie 
calcul cale, trasee cu latime de banda si latenta
mesaj - latenta / dimensiune mesaj ...

mapare soft pe hardware - actor pe host-urile care ruleaza
se face o rulare la sfarsit - calculat timpi
timpi global - duratia executie globala
- defalcare?? timpi de calcul si timpi de comunicatie
metrici finale: acceleratie, eficienta si cost
3 iteratii: secventiala, paralela, si imbunatatita

text - word in care se descrie proiectul
  introducere sintetizare probleme
    restrictii
    problema e paralelizabila pentru ca..
  sistem: arhitectura
    software: procese descompunere aplicatie in 
      calcule de tip - accelerare
      tip aplicatie => tip hardware
      schema arhitectura??
  simulare
    actori
      cod anexat
    cost 
    schema sugestiva
  rezultate simulare

  slide-uri cum arata sistemul - poze?
  simulare actori host-uri scheme

  exemple tutoriale simulator            

3 fisiere de la simulare
fisiere sursa
powerpoint - rezumat al ceea ce avem


