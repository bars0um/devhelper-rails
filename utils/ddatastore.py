import utils.states as states

class DataStore:
    def __init__(self, callback=None):
        self.callback = callback
        
        # Initial values
        self.last_assistant_message = False
        self.next_step = states.UNINITIALIZED
        self.specific_file_code = ""
        self.loaded_files = []
        self.app_files = []
        self.done_queue = []
        self.update_queue = []
        self.task_relevant_files = []
        self.project_folder = ""
        self.diagnose_error = ""
        self.last_linter_error = ""
        self.code = ""
        self.queue = []
        self.update_directive = ""
        self.update_plan = ""
        self.project_description = ""  # TODO: Remove
        self.task_relevant_code = ""
        self.epic = ""
        self.app_name = "myapp"
        self.bug_type = ""
        self.buggy_code = ""
        self.bug_details = ""
        self.code_summary = {}
        self.file_to_summarize = ""

    def __setattr__(self, name, value):
        """
        Intercept attribute assignments and trigger callback for data attributes.
        """
        # List of attributes that should trigger callbacks
        allowed_attrs = (
            'last_assistant_message',
            'next_step',
            'specific_file_code',
            'loaded_files',
            'app_files',
            'done_queue',
            'update_queue',
            'task_relevant_files',
            'project_folder',
            'diagnose_error',
            'last_linter_error',
            'code',
            'queue',
            'update_directive',
            'update_plan',
            'project_description',
            'task_relevant_code',
            'epic',
            'app_name',
            'buggy_code',
            'bug_type',
            'bug_details',
            'code_summary',
            'file_to_summarize'
        )

        if name in allowed_attrs:
            super().__setattr__(name, value)
            if self.callback:
                self.callback(name, value)
        else:
            # For other attributes, just set normally
            super().__setattr__(name, value)

# Example usage:
# def my_callback(instance, attr_name, new_value):
#     print(f"Attribute {attr_name} was changed to {new_value}")
    
# store = DataStore(my_callback)
# store.last_assistant_message = True  # This will trigger the callback