import sys
from simgrid import Actor, SimgridError, Engine, Host

from APP.actors.camera_actor import CameraActor

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <platform_file.xml>")
        sys.exit(1)

    platform_file = sys.argv[1]

    # 1. Initialize SimGrid Engine
    engine = Engine(sys.argv)

    # 2. Load the Platform XML file
    try:
        engine.load_platform(platform_file)
        print(">>> Platform loaded successfully.")
    except SimgridError as e:
        print(f"Error loading platform '{platform_file}': {e}")
        sys.exit(1)

    # 3. Define Simulation Parameters & Mailbox Names (centralized)
    FRAME_SIZE_KB = 512
    FRAME_INTERVAL = 0.1 # 10 FPS
    ZONE1_PROC_MBS = ["z1_proc_mb_1", "z1_proc_mb_2", "z1_proc_mb_3", "z1_proc_mb_4"]
    # Define Zone 2, Zone 3 mailboxes if they exist
    DB_MB = "db_server_mb"
    ALERT_MB = "alert_server_mb"

    # 4. Deploy Actors onto Hosts from XML
    try:
        print(">>> Deploying actors...")
        # --- Deploy Zone 1 Actors ---
        # Static Assignment Example: Cam1->ProcMB1, Cam2->ProcMB2, Cam3->ProcMB2, Cam4->ProcMB1
        Actor.create("Cam_Z1_C1", Host.by_name("z1_camera_host_1"), CameraActor,
                     "Cam_Z1_C1", ZONE1_PROC_MBS[0], FRAME_SIZE_KB*1024, FRAME_INTERVAL)
        Actor.create("Cam_Z1_C2", Host.by_name("z1_camera_host_2"), CameraActor,
                     "Cam_Z1_C2", ZONE1_PROC_MBS[1], FRAME_SIZE_KB*1024, FRAME_INTERVAL)
        Actor.create("Cam_Z1_C3", Host.by_name("z1_camera_host_3"), CameraActor,
                     "Cam_Z1_C3", ZONE1_PROC_MBS[1], FRAME_SIZE_KB*1024, FRAME_INTERVAL)
        Actor.create("Cam_Z1_C4", Host.by_name("z1_camera_host_4"), CameraActor,
                     "Cam_Z1_C4", ZONE1_PROC_MBS[0], FRAME_SIZE_KB*1024, FRAME_INTERVAL)

        # Deploy Processing Nodes for Zone 1 (assuming ProcessingActor defined)
        for i in range(4):
             host_name = f"z1_processing_node_{i+1}"
             actor_name = f"Proc_Z1_N{i+1}"
             mailbox_name = ZONE1_PROC_MBS[i]
             # Actor.create(actor_name, Host.by_name(host_name), ProcessingActor,
             #             actor_name, mailbox_name, DB_MB, ALERT_MB, "zone_1") # Args for ProcessingActor

        # --- Deploy Zone 2 & Zone 3 Actors (if defined in XML) ---
        # ...

        # --- Deploy Core Service Actors (assuming DatabaseActor, AlertActor defined) ---
        # Actor.create("DBServer", Host.by_name("database_server"), DatabaseActor, "DBServer", DB_MB)
        # Actor.create("AlertRecv", Host.by_name("alert_server"), AlertActor, "AlertRecv", ALERT_MB)

        print(">>> Actors deployed.")

    except SimgridError as e:
        print(f"Error during actor deployment: {e}")
        sys.exit(1)
    except Exception as e: # Catch other potential errors like Host.by_name failing
        print(f"An unexpected error occurred during deployment: {e}")
        sys.exit(1)


    # 5. Run the Simulation
    print(">>> Starting simulation engine...")
    engine.run()

    # 6. Simulation Finished
    print(f">>> Simulation finished at time {Engine.clock:.3f}s.")