# ProcessingActor - Implementare pregătită pentru integrare cu acceleratoare
# - procesează cadre de la cameră
# - simulează detecția obiectelor și recunoașterea facială
# - comunică cu baza de date și sistemul de alertă
# - conține scheme pentru viitoarea comunicare cu acceleratoarele

from simgrid import Mailbox, this_actor, SimgridError, Engine, Host
import random

class ProcessingActor:
    def __init__(self, processing_node: str, camera: str, database_mailbox_name: str, 
                 alert_mailbox_name: str, frame_size: int, zone_id: str):
        """
        processing_node: Name of the processing node.
        camera: Name of the camera actor.
        database_mailbox_name: Mailbox name of the DatabaseActor.
        alert_mailbox_name: Mailbox name of the AlertActor.
        frame_size: Size of the frame data in bytes.
        zone_id: ID of the zone this processing actor is responsible for.
        """
        
        self.processing_node = processing_node
        self.mailbox = Mailbox.by_name(processing_node)
        self.camera = camera
        self.database_mailbox_name = database_mailbox_name
        self.alert_mailbox_name = alert_mailbox_name
        self.frame_size = frame_size
        self.zone_id = zone_id
        
        # Extragerea resurselor computaționale disponibile
        host = Host.by_name(processing_node)
        self.host_speed = host.speed  # Viteza de procesare în FLOPS
        
        # Parametri pentru paralelizare și performanță adaptați la resursele disponibile
        if self.host_speed >= 1e12:  # 1 Tflops sau mai mult
            self.od_parallelism = 8  # Paralelism ridicat pentru OD
            self.fr_parallelism = 16  # Paralelism foarte ridicat pentru FR
        else:  # Pentru procesoare mai slabe
            self.od_parallelism = 2  # Paralelism redus
            self.fr_parallelism = 4  # Paralelism moderat
        
        # Parametri pentru simularea costurilor computaționale
        self.base_od_flops = 5000  # Flops de bază pentru detecția de obiecte
        self.base_fr_flops = 20000  # Flops de bază pentru recunoaștere facială
        
        # Inițializare mailbox-uri
        try:
            self.database_mailbox = Mailbox.by_name(self.database_mailbox_name)
            self.alert_mailbox = Mailbox.by_name(self.alert_mailbox_name)
        except SimgridError as e:
            this_actor.error(f"Mailbox {self.database_mailbox_name} or {self.alert_mailbox_name} not found for processing node {self.processing_node}.")
            raise e
            
        # SCHEMA PENTRU VIITOAREA INTEGRARE CU ACCELERATOARE
        # În viitor, aici se vor inițializa mailbox-urile pentru comunicarea cu acceleratoarele:
        # self.od_accelerator_mailbox = None  # Mailbox pentru acceleratorul de Object Detection
        # self.fr_accelerator_mailbox = None  # Mailbox pentru acceleratorul de Facial Recognition
    
    def __call__(self):
        """
        Funcția principală a actorului de procesare.
        """
        this_actor.info(f"Started on {self.processing_node}. Waiting for frames from {self.camera} ({self.frame_size} bytes) on {self.mailbox} at {Engine.clock:.3f}")
        this_actor.info(f"Using computational resources: {self.host_speed/1e12:.2f} TFlops, OD parallelism: {self.od_parallelism}, FR parallelism: {self.fr_parallelism}")
        
        while True:
            try:
                # 1. Primește un cadru de la camera 
                frame = self.mailbox.get()
                this_actor.info(f"Received frame '{frame}' from {self.camera} at {Engine.clock:.3f}")
                
                # SCHEMA PENTRU ACCELERATOARE: În viitor, codul ar putea fi modificat astfel:
                # self.od_accelerator_mailbox.put(f"OD_Task:{frame},{self.processing_node}", self.frame_size)
                # od_result = self.mailbox.get()  # Așteaptă răspunsul de la accelerator
                
                # 2. Deocamdată, procesăm local cadrul în paralel
                frame_results = self.process_frame_parallel(frame)
                
                # 3. Verifică dacă a fost detectată o persoană
                if frame_results["person_detected"]:
                    this_actor.info(f"Person detected in frame '{frame}' at coordinates {frame_results['person_coordinates']}.")
                    
                    # 4. Verifică dacă a fost recunoscută o față
                    if frame_results["face_id"] != "unknown_face":
                        # 5. Verifică autorizarea în baza de date
                        authorized = self.query_database(frame_results["face_id"])
                        
                        if not authorized:
                            this_actor.warning(f"Unauthorized access for Face ID: {frame_results['face_id']} in zone {self.zone_id} at {Engine.clock:.3f}")
                            self.send_alert(frame, frame_results["face_id"])
                        else:
                            this_actor.info(f"Authorized access for Face ID: {frame_results['face_id']} in zone {self.zone_id} at {Engine.clock:.3f}")
                    else:
                        # Față necunoscută - trimite alertă
                        this_actor.warning(f"Unknown face detected in zone {self.zone_id} at {Engine.clock:.3f}")
                        self.send_alert(frame, "unknown_face")
                else:
                    this_actor.info(f"No person detected in frame '{frame}'.")
                
            except SimgridError as e:
                this_actor.error(f"Error while processing frame: {e}")
                break
                
        this_actor.info(f"Stopping processing actor on {self.processing_node}.")
    
    def process_frame_parallel(self, frame):
        """
        Procesează cadrul în paralel, rulând detecția de obiecte și recunoașterea facială.
        
        NOTĂ: În viitor, această funcție va fi înlocuită cu comunicarea către acceleratoare.
        """
        results = {
            "person_detected": False,
            "person_coordinates": None,
            "face_id": "unknown_face"
        }
        
        # Execută detecția de obiecte
        detection_results = self.run_object_detection(frame)
        results["person_detected"] = detection_results["person_detected"]
        results["person_coordinates"] = detection_results["coordinates"]
        
        # Dacă a fost detectată o persoană, rulează recunoașterea facială
        if results["person_detected"]:
            face_result = self.run_facial_recognition(frame, detection_results["coordinates"])
            results["face_id"] = face_result
            
        return results
    
    def run_object_detection(self, frame):
        """
        Execută detecția de obiecte pe cadrul primit.
        
        NOTĂ: În viitor, această funcție va fi mutată în AcceleratorActor_OD.
        """
        flops_od = self.calculate_flops_od()
        detection_result = {
            "person_detected": False,
            "coordinates": None
        }
        
        try:
            # Calculăm costul per task, scale-at la viteza host-ului
            cost_per_task = flops_od / self.od_parallelism
            
            # Variație bazată pe host speed pentru simularea GPU acceleration
            if self.host_speed >= 1e12:  # 1 Tflops sau mai mult (GPU)
                cost_per_task = cost_per_task * 0.1  # GPU execută mult mai rapid
                
            # Simulează execuția paralelizată 
            this_actor.execute(cost_per_task)
            
            # Simulează detecția persoanelor
            detection_result = self.simulate_person_detection(frame)
            
            if detection_result["person_detected"]:
                this_actor.info(f"OD Result: Person FOUND at coordinates {detection_result['coordinates']}.")
            else:
                this_actor.info("OD Result: No person detected.")
        
        except SimgridError as e:
            this_actor.error(f"Error during object detection: {e}")
            return {"person_detected": False, "coordinates": None}
       
        return detection_result
    
    def run_facial_recognition(self, frame, person_coordinates):
        """
        Execută recunoașterea facială pe regiunea cadului unde a fost detectată o persoană.
        
        NOTĂ: În viitor, această funcție va fi mutată în AcceleratorActor_FR.
        """
        flops_fr = self.calculate_flops_fr()
        face_id = "unknown_face"
        
        try:
            # Calculăm costul per task, scale-at la viteza host-ului
            cost_per_task = flops_fr / self.fr_parallelism
            
            # Variație bazată pe host speed pentru simularea GPU acceleration
            if self.host_speed >= 1e12:  # 1 Tflops sau mai mult (GPU)
                cost_per_task = cost_per_task * 0.05  # GPU accelerează și mai mult FR
                
            # Simulează execuția paralelizată
            this_actor.execute(cost_per_task)
            
            # Simulează recunoașterea facială
            face_id = self.simulate_facial_recognition(frame, person_coordinates)
            this_actor.info(f"FR Result: Face ID: {face_id}")
            
        except SimgridError as e:
            this_actor.error(f"Error during facial recognition: {e}")
            return "unknown_face"
         
        return face_id
    
    def query_database(self, face_id):
        """
        Interoghează baza de date pentru a verifica dacă persoana identificată
        are acces la zona respectivă.
        """
        query_data = f"Query: {face_id}, Zone ID: {self.zone_id}"
        query_size = 1000
        
        try:
            this_actor.info(f"Querying database with Face ID: {face_id}, Zone: {self.zone_id} at {Engine.clock:.3f}")
            
            # Simulează timpul de pregătire a interogării
            query_setup_flops = 1000
            this_actor.execute(query_setup_flops)
            
            # Trimite interogarea către baza de date
            # Trimite și informații despre mailbox-ul propriu pentru a primi răspunsul
            full_query = f"{query_data},{self.processing_node}"
            this_actor.info(f"Sending query to database: {full_query}")
            self.database_mailbox.put(full_query, query_size)
            
            # Așteaptă răspunsul
            response = self.mailbox.get()
            this_actor.info(f"Received response from database: {response} at {Engine.clock:.3f}")
            
            # Verifică răspunsul
            return response == "Authorized"
            
        except SimgridError as e:
            this_actor.error(f"Error during database query: {e}")
            return False
    
    def send_alert(self, frame, face_id):
        """
        Trimite o alertă către sistemul de alertă în cazul accesului neautorizat.
        """
        alert_data = f"Alert: Unauthorized access in frame {frame}, Face ID: {face_id}, Zone: {self.zone_id}, Node: {self.processing_node}"
        alert_size = 2000
        
        try:
            this_actor.info(f"Sending alert: {alert_data} at {Engine.clock:.3f}")
            
            # Simulează timpul de pregătire a alertei
            alert_setup_flops = 2000
            this_actor.execute(alert_setup_flops)
            
            # Trimite alerta
            this_actor.info(f"Sending alert to {self.alert_mailbox}")
            self.alert_mailbox.put(alert_data, alert_size)
            return True
            
        except SimgridError as e:
            this_actor.error(f"Error during alert sending: {e}")
            return False
    
    def calculate_flops_od(self):
        """
        Calculează numărul de operații în virgulă mobilă necesare pentru detecția de obiecte.
        
        NOTĂ: În viitor, această funcție va fi mutată în AcceleratorActor_OD.
        """
        # Formula ia în calcul dimensiunea cadrului și o constantă de bază
        base_flops = self.base_od_flops * (self.frame_size / 1000)
        
        # Ajustăm în funcție de modelul simulat (presupunem că folosim YOLOv3)
        model_factor = 5e9  # 5 GFLOPS pentru YOLOv3 pe rezoluție standard
        
        # Reducem costul pentru rezoluții mici, creștem pentru rezoluții mari
        if self.frame_size < 500000:  # < 500KB (rezoluție mică)
            resolution_factor = 0.5
        elif self.frame_size > 2000000:  # > 2MB (rezoluție mare)
            resolution_factor = 2.0
        else:
            resolution_factor = 1.0
            
        return base_flops + (model_factor * resolution_factor)
    
    def calculate_flops_fr(self):
        """
        Calculează numărul de operații în virgulă mobilă necesare pentru recunoașterea facială.
        
        NOTĂ: În viitor, această funcție va fi mutată în AcceleratorActor_FR.
        """
        # Formula ia în calcul dimensiunea cadrului și o constantă de bază
        base_flops = self.base_fr_flops * (self.frame_size / 1000)
        
        # Ajustăm în funcție de modelul simulat (presupunem că folosim FaceNet)
        model_factor = 2e10  # 20 GFLOPS pentru FaceNet pe rezoluție standard
        
        # Reducem costul pentru rezoluții mici, creștem pentru rezoluții mari
        if self.frame_size < 500000:  # < 500KB (rezoluție mică)
            resolution_factor = 0.5
        elif self.frame_size > 2000000:  # > 2MB (rezoluție mare)
            resolution_factor = 2.0
        else:
            resolution_factor = 1.0
            
        return base_flops + (model_factor * resolution_factor)
    
    def simulate_person_detection(self, frame):
        """
        Simulează procesul de detecție a persoanelor.
        
        NOTĂ: În viitor, această funcție va fi mutată în AcceleratorActor_OD.
        """
        # Extragem ora din simulare pentru a modifica probabilitatea (simulăm zi/noapte)
        current_time = Engine.clock % 86400  # secundele într-o zi (24h * 60m * 60s)
        day_time = current_time > 25200 and current_time < 68400  # Între 7:00 și 19:00
        
        # Probabilitatea de bază de a detecta o persoană
        base_probability = 0.7
        
        # Ajustăm probabilitatea în funcție de ora din zi (mai puține persoane noaptea)
        if not day_time:
            base_probability *= 0.5
            
        # Ajustăm și în funcție de zona de supraveghere (probabilități diferite în funcție de zonă)
        if "z1" in self.zone_id:
            zone_factor = 1.2  # Zonă cu trafic mare
        else:
            zone_factor = 0.8  # Zonă cu trafic redus
            
        final_probability = min(0.95, base_probability * zone_factor)  # Limitare la 95%
        
        # Simulăm detecția
        person_detected = random.random() < final_probability
        
        coordinates = None
        if person_detected:
            # Simulează coordonatele dreptunghiului care încadrează persoana detectată
            max_width = min(800, self.frame_size // 1000)
            max_height = min(600, self.frame_size // 1500)
            
            x_min = random.randint(0, max_width - 100)
            y_min = random.randint(0, max_height - 100)
            width = random.randint(50, 100)
            height = random.randint(100, 200)
            
            coordinates = [
                x_min,
                y_min,
                x_min + width,
                y_min + height
            ]
        
        return {
            "person_detected": person_detected,
            "coordinates": coordinates
        }
    
    def simulate_facial_recognition(self, frame, person_coordinates):
        """
        Simulează procesul avansat de recunoaștere facială.
        
        NOTĂ: În viitor, această funcție va fi mutată în AcceleratorActor_FR.
        """
        if not person_coordinates:
            return "unknown_face"
            
        # Simulăm detectarea feței în cadrul coordonatelor persoanei
        face_detected = self.simulate_face_detection(person_coordinates)
        if not face_detected:
            return "unknown_face"
            
        # Extragem ora din simulare pentru a simula condițiile de iluminare
        current_time = Engine.clock % 86400  # secundele într-o zi
        
        # Calculăm mai multe factori care influențează calitatea recunoașterii
        quality_factors = self.calculate_face_quality_factors(current_time, person_coordinates)
        
        # Calculăm scorul de încredere pentru recunoaștere bazat pe factorii de calitate
        confidence_score = self.calculate_recognition_confidence(quality_factors)
        
        # Simulăm recunoașterea facială bazată pe scorul de încredere
        recognition_threshold = 0.65
        face_recognized = confidence_score >= recognition_threshold
        
        if face_recognized:
            # Generăm un set de identități potențiale și alegem cea mai probabilă
            face_id = self.select_most_likely_identity(confidence_score, quality_factors)
            this_actor.info(f"Face recognized with confidence {confidence_score:.2f}, Face ID: {face_id}")
            return face_id
        else:
            # Putem face distincție între diferite motive pentru ne-recunoaștere
            if confidence_score > 0.4:  # Scor mediu, dar sub prag
                this_actor.info(f"Face similar to known faces (confidence: {confidence_score:.2f}) but below threshold")
                return "low_confidence_face"
            else:  # Scor foarte mic
                this_actor.info(f"Face not recognized in database (confidence: {confidence_score:.2f})")
                return "unknown_face"
    
    def simulate_face_detection(self, person_coordinates):
        """
        Simulează detectarea feței în cadrul coordonatelor persoanei.
        
        NOTĂ: În viitor, această funcție va fi mutată în AcceleratorActor_FR.
        """
        # Calculăm dimensiunea relativă a persoanei în cadru
        person_width = person_coordinates[2] - person_coordinates[0]
        person_height = person_coordinates[3] - person_coordinates[1]
        
        # Persoanele mici în cadru au șanse mai mici ca fața să fie detectabilă
        if person_width < 30 or person_height < 60:
            probability = 0.3  # Șansă mică pentru persoane mici/distante
        elif person_width > 100 and person_height > 200:
            probability = 0.95  # Șansă mare pentru persoane apropiate
        else:
            probability = 0.8  # Șansă medie pentru persoane la distanță moderată
            
        return random.random() < probability
    
    def calculate_face_quality_factors(self, current_time, person_coordinates):
        """
        Calculează factorii care influențează calitatea recunoașterii faciale.
        
        NOTĂ: În viitor, această funcție va fi mutată în AcceleratorActor_FR.
        """
        factors = {}
        
        # Factor de iluminare bazat pe ora din zi
        daylight_hour = (current_time / 3600) % 24
        if 7 <= daylight_hour <= 19:  # Zi
            base_illumination = 0.5 + 0.5 * (1 - abs(daylight_hour - 13) / 6)  # Max la ora 13:00
        else:  # Noapte
            # Simulăm iluminare artificială noaptea (mai slabă și mai constantă)
            base_illumination = 0.3
        factors['illumination'] = base_illumination
        
        # Factor de proximitate (cât de aproape e persoana)
        person_width = person_coordinates[2] - person_coordinates[0]
        person_height = person_coordinates[3] - person_coordinates[1]
        person_size = person_width * person_height
        max_expected_size = 800 * 600  # Dimensiune maximă așteptată
        proximity = min(1.0, person_size / max_expected_size)
        factors['proximity'] = proximity
        
        # Factor de claritate (simulat ca o funcție de dimensiunea cadrului)
        clarity = min(1.0, self.frame_size / 2000000)  # Raportăm la 2MB (Full HD)
        factors['clarity'] = clarity
        
        # Factor de ocluzie/unghi facial (simulat aleatoriu)
        occlusion = random.uniform(0.6, 1.0)  # Cel puțin 60% din față e vizibilă
        factors['occlusion'] = occlusion
        
        # Factor de deplasare/blur (simulat aleatoriu)
        motion = random.uniform(0.7, 1.0)  # Cel puțin 70% claritate (puțin blur)
        factors['motion'] = motion
        
        return factors
    
    def calculate_recognition_confidence(self, quality_factors):
        """
        Calculează scorul de încredere pentru recunoașterea facială
        bazat pe factorii de calitate.
        
        NOTĂ: În viitor, această funcție va fi mutată în AcceleratorActor_FR.
        """
        # Ponderi pentru diferiți factori (suma = 1.0)
        weights = {
            'illumination': 0.25,
            'proximity': 0.35,
            'clarity': 0.15,
            'occlusion': 0.15,
            'motion': 0.1
        }
        
        # Calculăm scorul ponderat
        weighted_score = sum(weights[factor] * quality_factors[factor] for factor in weights)
        
        # Adăugăm o componentă aleatoare pentru variabilitate (±15%)
        random_component = random.uniform(-0.15, 0.15)
        
        # Scorul final între 0.0 și 1.0
        final_score = max(0.0, min(1.0, weighted_score + random_component))
        
        return final_score
    
    def select_most_likely_identity(self, confidence_score, quality_factors):
        """
        Selectează cea mai probabilă identitate bazată pe scorul de recunoaștere
        și factorii de calitate.
        
        NOTĂ: În viitor, această funcție va fi mutată în AcceleratorActor_FR.
        """
        # Generăm ID-uri în funcție de zonă pentru a simula accesul bazat pe reguli
        zone_prefix = self.zone_id.replace("zone_", "").lower()
        
        # Diferite tipuri de utilizatori cu probabilități diferite
        user_types = [
            {"prefix": f"{zone_prefix}_employee_", "probability": 0.5, "authorized": True, "min_confidence": 0.65},
            {"prefix": f"{zone_prefix}_visitor_", "probability": 0.15, "authorized": False, "min_confidence": 0.7},
            {"prefix": f"{zone_prefix}_manager_", "probability": 0.2, "authorized": True, "min_confidence": 0.6},
            {"prefix": f"{zone_prefix}_security_", "probability": 0.1, "authorized": True, "min_confidence": 0.55},
            {"prefix": "unknown_person_", "probability": 0.05, "authorized": False, "min_confidence": 0.75}
        ]
        
        # Filtrăm tipurile de utilizatori bazat pe scorul de încredere minim necesar
        eligible_types = [t for t in user_types if confidence_score >= t["min_confidence"]]
        
        if not eligible_types:
            return "low_confidence_match"
            
        # Ajustăm probabilitățile bazate pe scorul de încredere și proximitate
        adjusted_types = []
        for user_type in eligible_types:
            # Managerii și personalul de securitate sunt mai ușor de recunoscut (au poze mai bune în baza de date)
            if "manager" in user_type["prefix"] or "security" in user_type["prefix"]:
                adjustment = 1.2
            # Vizitatorii sunt mai greu de recunoscut (poze mai vechi sau de calitate inferioară)
            elif "visitor" in user_type["prefix"]:
                adjustment = 0.8
            else:
                adjustment = 1.0
                
            # Proximitatea influențează major recunoașterea persoanelor necunoscute
            if "unknown" in user_type["prefix"] and quality_factors["proximity"] < 0.6:
                adjustment *= 0.5
                
            adjusted_prob = user_type["probability"] * adjustment
            adjusted_types.append({**user_type, "adjusted_probability": adjusted_prob})
            
        # Normalizăm probabilitățile ajustate
        total_prob = sum(t["adjusted_probability"] for t in adjusted_types)
        for t in adjusted_types:
            t["normalized_probability"] = t["adjusted_probability"] / total_prob
            
        # Selectăm tipul de utilizator bazat pe probabilitățile normalizate
        rand_val = random.random()
        cumulative_prob = 0
        selected_type = adjusted_types[-1]  # Default la ultimul tip
        
        for user_type in adjusted_types:
            cumulative_prob += user_type["normalized_probability"]
            if rand_val < cumulative_prob:
                selected_type = user_type
                break
                
        # Generăm un ID specific pentru tipul selectat
        user_id = f"{selected_type['prefix']}{random.randint(1, 999):03d}"
        
        return user_id

    # SCHEMA PENTRU VIITOAREA INTEGRARE CU ACCELERATOARE
    
    # Următoarele funcții vor fi adăugate în viitor pentru comunicarea cu acceleratoarele:
    
    # def offload_object_detection_to_accelerator(self, frame):
    #     """
    #     Trimite un cadru către acceleratorul OD și așteptă rezultatul.
    #     """
    #     # 1. Trimite cadrul la accelerator
    #     od_task_data = f"OD_Task:{frame},{self.processing_node}"
    #     self.od_accelerator_mailbox.put(od_task_data, self.frame_size)
    #     
    #     # 2. Așteaptă rezultatul (blocare/sincronizare)
    #     od_result = self.mailbox.get()
    #     
    #     # 3. Parsează rezultatul
    #     return self.parse_od_result(od_result)
    # 
    # def offload_facial_recognition_to_accelerator(self, frame, coordinates):
    #     """
    #     Trimite regiunea persoanei către acceleratorul FR și așteptă rezultatul.
    #     """
    #     # 1. Calculează dimensiunea regiunii (aproximativ 25% din cadrul original)
    #     region_size = int(self.frame_size * 0.25)
    #     
    #     # 2. Trimite regiunea la accelerator
    #     fr_task_data = f"FR_Task:{frame},{self.processing_node},{coordinates}"
    #     self.fr_accelerator_mailbox.put(fr_task_data, region_size)
    #     
    #     # 3. Așteaptă rezultatul (blocare/sincronizare)
    #     fr_result = self.mailbox.get()
    #     
    #     # 4. Parsează rezultatul
    #     return self.parse_fr_result(fr_result)
    # 
    # def parse_od_result(self, od_result):
    #     """
    #     Parsează rezultatul returnat de acceleratorul OD.
    #     Format așteptat: "OD_Result:{person_detected},{x1,y1,x2,y2}"
    #     """
    #     # Implementarea va fi adăugată mai târziu
    #     pass
    # 
    # def parse_fr_result(self, fr_result):
    #     """
    #     Parsează rezultatul returnat de acceleratorul FR.
    #     Format așteptat: "FR_Result:{face_id}"
    #     """
    #     # Implementarea va fi adăugată mai târziu
    #     pass