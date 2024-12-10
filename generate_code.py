import os
import numpy as np
import json


def get_var_code(symbol, shape, type, definition, solver="gurobipy"):
    """
    Generates code for defining variables in the optimization model.
    """
    if solver == "gurobipy":
        if shape == []:
            return f'{symbol} = model.addVar(vtype=GRB.{type.upper()}, name="{symbol}")\n'
        else:
            return (
                f"{symbol} = model.addVars(" 
                + ", ".join([str(i) for i in shape]) 
                + f', vtype=GRB.{type.upper()}, name="{symbol}")\n'
            )
    else:
        raise NotImplementedError(f"Solver {solver} is not implemented")


def generate_code(state, dir):
    code = []

    # Ensure parameters are in dictionary format
    if isinstance(state["parameters"], list):
        state["parameters"] = {
            f"param_{i}": {
                "shape": param.get("shape", []),
                "definition": param.get("definition", "")
            } if isinstance(param, dict) else {"shape": [], "definition": param}
            for i, param in enumerate(state["parameters"])
        }

#     code.append(
#         f"""
# import os
# import numpy as np
# import json 
# from gurobipy import Model, GRB, quicksum


# model = Model("OptimizationProblem")

# with open("data.json", "r") as f:
#     data = json.load(f)

# """
#     )

    code.append(f"""
import os
import numpy as np
import json 
from gurobipy import Model, GRB, quicksum


model = Model("OptimizationProblem")

"""
    )
    code.append("\n\n### Define the parameters\n")
    for symbol, v in state["parameters"].items():
        definition = v.get("definition", "")
        code.append(f'{symbol} = {definition}')

    code.append("\n\n### Define the variables\n")
    # Update this part to handle a list of variables
    for v in state.get("variables", []):  # Ensure variables is not None
        symbol = v.get("symbol")  # Assuming variable has a 'symbol' key
        shape = v.get("shape", [])
        type_ = v.get("type", "")
        definition = v.get("definition", "")
        code.append(
            get_var_code(
                symbol,
                shape,
                type_,
                definition,
                solver="gurobipy",
            )
        )

    code.append("\n\n### Define the constraints\n")
    for c in state.get("constraints", []):  # Ensure constraints is not None
        code.append(c.get("code", ""))  # If 'code' is None, use an empty string

    code.append("\n\n### Define the objective\n")
    code.append(state["objective"].get("code", ""))  # If 'code' is None, use an empty string

    code.append("\n\n### Optimize the model\n")
    code.append("model.optimize()\n")

    code.append("\n\n### Output optimal objective value\n")
    # code.append(f'print("Optimal Objective Value: ", model.objVal)\n')

    code.append(
        """
if model.status == GRB.OPTIMAL:
    with open("output_solution.txt", "w") as f:
        f.write(f"Optimal Objective Value: {model.objVal}")
        for var in model.getVars():
            f.write(f"{var.varName}: {var.x}")
        print("Optimal Objective Value: ", model.objVal)
        for var in model.getVars():
            print(f"{var.varName}: {var.x}")
else:
    with open("output_solution.txt", "w") as f:
        f.write(f"Model status: {model.status}")
    print("Model status: ", model.status)
"""
    )

    # Ensure all items in the code list are strings before joining
    code_str = "\n".join(str(line) if line is not None else "" for line in code)

    with open(os.path.join(dir, "code.py"), "w") as f:
        f.write(code_str)
