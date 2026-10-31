import inspect
import fc_clubs_api

print("PAKET:", fc_clubs_api.__file__)

for name, obj in inspect.getmembers(fc_clubs_api):
    if inspect.isclass(obj) or inspect.isfunction(obj):
        if not name.startswith("_"):
            print("\n", name)
            if inspect.isclass(obj):
                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                    if not method_name.startswith("_"):
                        try:
                            print("  ", method_name, inspect.signature(method))
                        except (ValueError, TypeError):
                            print("  ", method_name)
