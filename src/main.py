import sys
from APP.actors.alert_actor import AlertActor
from APP.actors.camera_actor import CameraActor
from APP.actors.database_actor import DatabaseActor
from APP.actors.dispatcher_actor import DispatcherActor
from actors.processing_actor import ProcessingActor
from simgrid import Actor, SimgridError, Engine, Host, Mailbox 


if __name__ == '__main__':
    platform_file = "platform.xml"

    engine = Engine()

    try:
        engine.load_platform(platform_file)
        print(">>> Platform loaded successfully.")
    except SimgridError as e:
        print(f"Error loading platform '{platform_file}': {e}")
        sys.exit(1)


    FRAME_SIZE_BYTES = 1024 * 1024
    CAPTURE_INTERVAL = 0.5     

    DISPATCHER_MAILBOX = "dispatcher_mailbox"
    DATABASE_MAILBOX = "database_server_mailbox"
    ALERT_MAILBOX = "alert_server_malibox"

    Z1_PROC_MBS = [f"z1_proc_mb_{i+1}" for i in range(4)] 

    Z1_CAMERA_HOSTS = [f"z1_camera_host_{i+1}" for i in range(4)]
    Z1_PROC_HOSTS = [f"z1_processing_node_{i+1}" for i in range(4)]

    CORE_ROUTER_HOST = "core_router"
    DATABASE_SERVER_HOST = "database_server"
    ALERT_SERVER_HOST = "alert_server"

    try:
        print(">>> Deploying actors...")

        Actor.create("Dispatcher", Host.by_name(CORE_ROUTER_HOST), DispatcherActor, DISPATCHER_MAILBOX) 

        for i in range(len(Z1_PROC_HOSTS)):
            actor_name = f"Proc_Z1_N{i+1}"
            host_name = Z1_PROC_HOSTS[i]
            my_unique_mailbox = Z1_PROC_MBS[i]
            Actor.create(actor_name, Host.by_name(host_name), ProcessingActor,
                         actor_name, my_unique_mailbox, DISPATCHER_MAILBOX, DATABASE_MAILBOX, ALERT_MAILBOX)

        Actor.create("Cam_Z1_C1", Host.by_name(Z1_CAMERA_HOSTS[0]), CameraActor,
                     "Cam_Z1_C1", "zone_1", DISPATCHER_MAILBOX, FRAME_SIZE_BYTES, CAPTURE_INTERVAL)
        Actor.create("Cam_Z1_C2", Host.by_name(Z1_CAMERA_HOSTS[1]), CameraActor,
                     "Cam_Z1_C2", "zone_1", DISPATCHER_MAILBOX, FRAME_SIZE_BYTES, CAPTURE_INTERVAL)
        Actor.create("Cam_Z1_C3", Host.by_name(Z1_CAMERA_HOSTS[2]), CameraActor,
                     "Cam_Z1_C3", "zone_1", DISPATCHER_MAILBOX, FRAME_SIZE_BYTES, CAPTURE_INTERVAL)
        Actor.create("Cam_Z1_C4", Host.by_name(Z1_CAMERA_HOSTS[3]), CameraActor,
                     "Cam_Z1_C4", "zone_1", DISPATCHER_MAILBOX, FRAME_SIZE_BYTES, CAPTURE_INTERVAL)

        Actor.create("DBServer", Host.by_name(DATABASE_SERVER_HOST), DatabaseActor,DATABASE_MAILBOX)
        Actor.create("AlertRecv", Host.by_name(ALERT_SERVER_HOST), AlertActor, ALERT_MAILBOX) 

        print(">>> Actors deployed.")

    except SimgridError as e:
        print(f"Error during actor deployment: {e}")
        sys.exit(1)
    except Exception as e: 
        print(f"An unexpected error occurred during deployment: {e}")
        sys.exit(1)

    print(">>> Starting simulation engine...")
    engine.run()

    print(f">>> Simulation finished at time {Engine.clock:.3f}s.")