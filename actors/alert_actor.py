from simgrid import Mailbox, this_actor, Engine

class AlertActor:
    def __init__(self, alert_server: str):
        """
        alert_server: Name of the alert server.
        """
        
        self.alert_server = alert_server
        self.alert_mailbox = Mailbox.by_name(alert_server)
        
    def __call__(self):
        this_actor.info(f"Started. Waiting for alerts on {self.alert_mailbox} at {Engine.clock:.3f}")
        
        while True:
            try:
                alert_data = self.alert_mailbox.get()
                
                this_actor.info(f"Received alert '{alert_data}' at {Engine.clock:.3f}")
                
                flops_alert_log = 500
                this_actor.execute(flops_alert_log)
                
            except Exception as e:
                this_actor.error(f"Error while processing alert: {e}")
                break