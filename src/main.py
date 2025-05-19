import sys
from simgrid import Actor, Engine, Host

from APP.actors.camera_actor import CameraActor
from APP.actors.dispatcher_actor import DispatcherActor
from APP.actors.processing_cpu_actor import ProcessingActorCPU 
from APP.actors.accelerator_od_actor import AcceleratorActorOD
from APP.actors.accelerator_fr_actor import AcceleratorActorFR
from APP.actors.database_actor import DatabaseActor
from APP.actors.alert_actor import AlertActor

if __name__ == '__main__':
    if len(sys.argv) != 2: 
        print(f"Usage: python {sys.argv[0]} <platform_file.xml>")
        sys.exit(1)
        
    platform_file = sys.argv[1]
    engine = Engine(sys.argv)

    try:
        engine.load_platform(platform_file)
        print(">>> Platform loaded successfully.")
        
    except Exception as e:
        print(f"Error loading platform '{platform_file}': {e}")
        sys.exit(1)

    FRAME_SIZE_BYTES = 1024 * 1024      
    CAPTURE_INTERVAL = 0.05          
    MAX_FRAMES_PER_CAMERA = 1000       

    DISPATCHER_MB_NAME = "dispatcher_main_mb"
    DB_MB_NAME = "db_server_main_mb"
    ALERT_MB_NAME = "alert_server_main_mb"

    CAMERAS_PER_ZONE = { "zone_1": 4, "zone_2": 2, "zone_3": 3 }
    SEQUENTIAL_MODE = False
    PROCESSING_UNITS_PER_ZONE = { "zone_1": 1 if SEQUENTIAL_MODE else 8 , "zone_2": 2, "zone_3": 2 } 

    CORE_ROUTER_HOST = "core_router"
    DB_SERVER_HOST = "database_server"
    ALERT_SERVER_HOST = "alert_server"

    try:
        print(">>> Deploying actors...")

        Actor.create("Dispatcher", Host.by_name(CORE_ROUTER_HOST), lambda: DispatcherActor(DISPATCHER_MB_NAME)())
        Actor.create("DBServer", Host.by_name(DB_SERVER_HOST), lambda: DatabaseActor(DB_MB_NAME)()) 
        Actor.create("AlertRecv", Host.by_name(ALERT_SERVER_HOST), lambda: AlertActor(ALERT_MB_NAME)())

        for zone_num in [1]:
            zone_id = f"zone_{zone_num}"
            num_cameras = CAMERAS_PER_ZONE.get(zone_id, 0)
            num_proc_units = PROCESSING_UNITS_PER_ZONE.get(zone_id, 0)

            print(f">>> Deploying actors for {zone_id}...")

            for i in range(num_proc_units):
                unit_idx = i + 1
                
                cpu_host_name = f"z{zone_num}_cpu_node_{unit_idx}"
                od_accel_host_name = f"z{zone_num}_accelerator_od_{unit_idx}"
                fr_accel_host_name = f"z{zone_num}_accelerator_fr_{unit_idx}"

                cpu_actor_name = f"CPU_Z{zone_num}_P{unit_idx}"
                od_accel_actor_name = f"OD_Accel_Z{zone_num}_{unit_idx}"
                fr_accel_actor_name = f"FR_Accel_Z{zone_num}_{unit_idx}"
                
                cpu_mb_name = f"cpu_z{zone_num}_p{unit_idx}_mb"
                od_accel_mb_name = f"od_accel_z{zone_num}_{unit_idx}_mb"
                fr_accel_mb_name = f"fr_accel_z{zone_num}_{unit_idx}_mb"

                Actor.create(od_accel_actor_name, Host.by_name(od_accel_host_name),
                            lambda name=od_accel_actor_name, mb=od_accel_mb_name: AcceleratorActorOD(name, mb)())

                Actor.create(fr_accel_actor_name, Host.by_name(fr_accel_host_name),
                            lambda name=fr_accel_actor_name, mb=fr_accel_mb_name: AcceleratorActorFR(name, mb)())

                Actor.create(cpu_actor_name, Host.by_name(cpu_host_name),
                            lambda name=cpu_actor_name, mb=cpu_mb_name, zone=zone_id, od_mb=od_accel_mb_name, fr_mb=fr_accel_mb_name:
                                ProcessingActorCPU(name, mb, DISPATCHER_MB_NAME, DB_MB_NAME, ALERT_MB_NAME, od_mb, fr_mb)())  

            for i in range(num_cameras):
                cam_idx = i + 1
                cam_actor_name = f"Cam_Z{zone_num}_C{cam_idx}"
                cam_host_name = f"z{zone_num}_camera_host_{cam_idx}"
                
                Actor.create(cam_actor_name, Host.by_name(cam_host_name),
                            lambda name=cam_actor_name, zone=zone_id: 
                                CameraActor(name, zone, DISPATCHER_MB_NAME, FRAME_SIZE_BYTES, CAPTURE_INTERVAL, MAX_FRAMES_PER_CAMERA)())


        print(">>> All actors deployed.")

    except Exception as e: 
        print(f"An unexpected error occurred during deployment: {e} (Host name mismatch with XML?)")
        sys.exit(1)

    print(">>> Starting simulation engine...")
    engine.run()

    print(f">>> Simulation finished at time {Engine.clock:.3f}s.")