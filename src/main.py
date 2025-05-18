import sys
from simgrid import Actor, Engine, Host, Mailbox

# --- IMPORT YOUR ACTUAL ACTOR CLASSES ---
# Make sure these paths are correct relative to where you run main.py
# For example, if your 'APP' folder is in the same directory as main.py:
from APP.actors.camera_actor import CameraActor
from APP.actors.dispatcher_actor import DispatcherActor
# Assuming ProcessingActor is the CPU part, let's rename for clarity
from APP.actors.processing_cpu_actor import ProcessingActorCPU # You might need to create/rename this
# You will need to create these accelerator actor classes:
from APP.actors.accelerator_od_actor import AcceleratorActorOD
from APP.actors.accelerator_fr_actor import AcceleratorActorFR
from APP.actors.database_actor import DatabaseActor
from APP.actors.alert_actor import AlertActor

if __name__ == '__main__':
    if len(sys.argv) != 2: # Ensure platform file is passed as argument
        print(f"Usage: python {sys.argv[0]} <platform_file.xml>")
        sys.exit(1)
    platform_file = sys.argv[1]

    engine = Engine(sys.argv) # Pass sys.argv to Engine

    try:
        engine.load_platform(platform_file)
        print(">>> Platform loaded successfully.")
    except Exception as e:
        print(f"Error loading platform '{platform_file}': {e}")
        sys.exit(1)

    # --- Simulation Configuration ---
    FRAME_SIZE_BYTES = 1024 * 1024      # 1MB for high-res frame data
    CAPTURE_INTERVAL = 0.1              # 10 FPS
    MAX_FRAMES_PER_CAMERA = 100         # For controlled experiment duration (optional)

    # --- Mailbox Naming Conventions ---
    DISPATCHER_MB_NAME = "dispatcher_main_mb"
    DB_MB_NAME = "db_server_main_mb"
    ALERT_MB_NAME = "alert_server_main_mb"

    # --- Define Number of Components per Zone (Example) ---
    # You can adjust these numbers based on your XML platform
    CAMERAS_PER_ZONE = { "zone_1": 4, "zone_2": 2, "zone_3": 3 }
    PROCESSING_UNITS_PER_ZONE = { "zone_1": 4, "zone_2": 2, "zone_3": 2 } # "Unit" = 1 CPU + 1 OD Accel + 1 FR Accel

    # --- Central Host Names ---
    CORE_ROUTER_HOST = "core_router"
    DB_SERVER_HOST = "database_server"
    ALERT_SERVER_HOST = "alert_server"

    try:
        print(">>> Deploying actors...")

        # --- Deploy Dispatcher Actor ---
        Actor.create("Dispatcher", Host.by_name(CORE_ROUTER_HOST), DispatcherActor,
                     DISPATCHER_MB_NAME) # Args for DispatcherActor: its_mailbox_name

        # --- Deploy Core Service Actors ---
        Actor.create("DBServer", Host.by_name(DB_SERVER_HOST), DatabaseActor,
                     DB_MB_NAME) # Args for DatabaseActor: its_mailbox_name
        Actor.create("AlertRecv", Host.by_name(ALERT_SERVER_HOST), AlertActor,
                     ALERT_MB_NAME)   # Args for AlertActor: its_mailbox_name

        # --- Deploy Actors for Each Zone ---
        for zone_num in [1]: # For zone_1, zone_2, zone_3
            zone_id = f"zone_{zone_num}"
            num_cameras = CAMERAS_PER_ZONE.get(zone_id, 0)
            num_proc_units = PROCESSING_UNITS_PER_ZONE.get(zone_id, 0)

            print(f">>> Deploying actors for {zone_id}...")

            # Deploy Processing Units (CPU + OD Accelerator + FR Accelerator)
            for i in range(num_proc_units):
                unit_idx = i + 1
                
                # Define names and mailboxes for this processing unit
                cpu_host_name = f"z{zone_num}_cpu_node_{unit_idx}"
                od_accel_host_name = f"z{zone_num}_accelerator_od_{unit_idx}"
                fr_accel_host_name = f"z{zone_num}_accelerator_fr_{unit_idx}"

                cpu_actor_name = f"CPU_Z{zone_num}_P{unit_idx}"
                od_accel_actor_name = f"OD_Accel_Z{zone_num}_{unit_idx}"
                fr_accel_actor_name = f"FR_Accel_Z{zone_num}_{unit_idx}"
                
                cpu_mb_name = f"cpu_z{zone_num}_p{unit_idx}_mb"
                od_accel_mb_name = f"od_accel_z{zone_num}_{unit_idx}_mb"
                fr_accel_mb_name = f"fr_accel_z{zone_num}_{unit_idx}_mb"

                # Deploy Accelerators first (they need to be ready to receive tasks)
                Actor.create(od_accel_actor_name, Host.by_name(od_accel_host_name), AcceleratorActorOD,
                             od_accel_actor_name, od_accel_mb_name) # Args: name, my_mailbox
                Actor.create(fr_accel_actor_name, Host.by_name(fr_accel_host_name), AcceleratorActorFR,
                             fr_accel_actor_name, fr_accel_mb_name) # Args: name, my_mailbox
                
                # Deploy CPU part of Processing Node
                Actor.create(cpu_actor_name, Host.by_name(cpu_host_name), ProcessingActorCPU,
                             cpu_actor_name,      # name
                             cpu_mb_name,         # my_mailbox_name (for dispatcher to send tasks to)
                             DISPATCHER_MB_NAME,  # dispatcher_mailbox_name (to send "ready" messages)
                             DB_MB_NAME,          # db_mailbox_name
                             ALERT_MB_NAME,       # alert_mailbox_name
                             zone_id,             # zone_id
                             od_accel_mb_name,    # od_accelerator_mailbox_name
                             fr_accel_mb_name)    # fr_accelerator_mailbox_name

            # Deploy Camera Actors for this zone
            for i in range(num_cameras):
                cam_idx = i + 1
                cam_actor_name = f"Cam_Z{zone_num}_C{cam_idx}"
                cam_host_name = f"z{zone_num}_camera_host_{cam_idx}" # From your XML
                
                Actor.create(cam_actor_name, Host.by_name(cam_host_name), CameraActor,
                             cam_actor_name,        # name
                             zone_id,               # zone_id
                             DISPATCHER_MB_NAME,    # dispatcher_mailbox_name
                             FRAME_SIZE_BYTES,
                             CAPTURE_INTERVAL,
                             MAX_FRAMES_PER_CAMERA) # Pass max_frames

        print(">>> All actors deployed.")

    except Exception as e: 
        print(f"An unexpected error occurred during deployment: {e} (Host name mismatch with XML?)")
        sys.exit(1)

    # 5. Run the Simulation
    print(">>> Starting simulation engine...")
    engine.run()

    # 6. Simulation Finished
    print(f">>> Simulation finished at time {Engine.clock:.3f}s.")