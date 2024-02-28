import glob
from protocol_settings import protocol_settings

settings_dir = 'protocols'

protocol_names : list[str] = []
protcols : dict[str,protocol_settings] = {}

for file in glob.glob(settings_dir + "/*.json"):
    file = file.lower().replace(settings_dir, '').replace('/', '').replace('\\', '').replace('\\', '').replace('.json', '')
    print(file)
    protocol_names.append(file)


max_input_register : int = 0
max_holding_register : int = 0

for name in protocol_names:
    protcols[name] = protocol_settings(name)

    if protcols[name].input_registry_size > max_input_register:
        max_input_register = protcols[name].input_registry_size

    if protcols[name].input_registry_size > max_holding_register:
        max_holding_register = protcols[name].holding_registry_size

print("max input register: ", max_input_register)
print("max holding register: ", max_holding_register)