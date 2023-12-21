from data_manager import DataManagement

data_manager=DataManagement()
data_manager.reset_data_except_instructions()
data_manager.set_prompt(f"What is the capital of the UnitedStates?")
data_manager.save_to_json()

