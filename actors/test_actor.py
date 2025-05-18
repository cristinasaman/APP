# In main.py, or a new file like simple_actor.py
from simgrid import this_actor, Actor, Host # ensure Actor and Host are imported if used here

class SimpleTestActor:
    def __init__(self, name):
        self.name = name
        this_actor.info(f"SimpleTestActor '{self.name}' __init__ called.")

    def __call__(self):
        # THIS IS THE CRITICAL LOG. If it doesn't show, __call__ isn't being entered or exits before this.
        this_actor.info(f"SimpleTestActor '{this_actor.get_name()}' __call__ STARTED. SimTime: {Engine.clock:.3f}s")
        try:
            this_actor.sleep_for(1.0)
            this_actor.info(f"SimpleTestActor '{this_actor.get_name()}' WOKE after 1.0s. SimTime: {Engine.clock:.3f}s")
            this_actor.sleep_for(2.0)
            this_actor.info(f"SimpleTestActor '{this_actor.get_name()}' WOKE after 2.0s. SimTime: {Engine.clock:.3f}s. FINISHING.")
        except Exception as e:
            this_actor.error(f"SimpleTestActor '{this_actor.get_name()}' CRASHED in __call__: {e}")
            # rais