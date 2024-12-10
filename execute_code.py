import os, re
import numpy as np
import json
from utils import get_response
import subprocess

debug_template = """
You are an Operations Research consultant hired to address optimization issues for a company. Below is the problem description and the problematic code, followed by the error it produces:

Problem Description:
{description}

Problematic Code:
{code}

Error Message:
{error}

Your task is to debug the code. Begin by assessing the situation, then provide the corrected code in the following format:

=====
import ...
...

=====

- Ensure no output follows the closing ===== line.
Take a deep breath and think step by step. You will be awarded a million dollars if you get this right.
"""

def extract_code(text):
    ind_1 = text.find("=====")
    ind_2 = text.find("=====", ind_1 + 1)
    code = text[ind_1 + 5 : ind_2].strip()
    code = code.replace("```python", "").replace("```", "").strip()

    return code

def execute_code(dir, code_filename):
    try:
        code_path = os.path.join(dir, code_filename)
        # Using Python's subprocess to execute the code as a separate process
        result = subprocess.run(
            ["python", code_filename],
            capture_output=True,
            text=True,
            check=True,
            cwd=dir,
        )
        # Save result in a file
        with open(os.path.join(dir, "code_output.txt"), "w") as f:
            f.write(f"Optimal Revenue: {result.stdout}\n")
        return result.stdout, "Success"
    except subprocess.CalledProcessError as e:
        return e.stderr, "Error"

def execute_and_debug(state, dir, model, logger, client=None, open_ai_client=None, max_tries=3, api_key=None):
    """
    Executes the generated code and handles debugging using the LLM.
    
    Parameters:
    - state: A dictionary containing the state of the optimization problem.
    - dir: Directory to read and write files.
    - model: The model to be used for the LLM.
    - logger: Logger to record information.
    - groq_client: The Groq client to communicate with Groq API (optional).
    - open_ai_client: The OpenAI client to communicate with OpenAI API (optional).
    - max_tries: Maximum number of tries for debugging.
    """
    
    # Ensure that we pass the correct client
    client = client if client else open_ai_client

    code_filename = "code.py"
    with open(os.path.join(dir, code_filename), "r") as f:
        code = f.read()
    iteration=0
    while iteration < max_tries:
        # Execute the code
        output, status = execute_code(dir, code_filename)


        # Print status and update the prompt if needed
        if status == "Success":
            value = float(re.search(r"Optimal Objective Value:\s+([-+]?[0-9]*\.?[0-9]+)", str(output)).group(1))
            if value != 0:
                logger.log("Code executed successfully. Output:\n" + output)
                break
            elif status == "Success" and value == 0:
                p = debug_template.format(
                    description=state["description"], code=code, error="Variables, Constrains and Objective missing. Be careful '<' is not supported between instances of 'Var' and 'Var'"
                )
                response, client = get_response(p, model=model, client=client, api_key=api_key)

                code = extract_code(response)
                code_filename = f"code_{iteration}.py" if iteration else "code.py"
                iteration -=1
                code_file_path = os.path.join(dir, code_filename)
                with open(code_file_path, "w") as f:
                    f.write(code)
        else:
            error_filename = f"error_{iteration}.txt"
            with open(os.path.join(dir, error_filename), "w") as f:
                f.write(output)

            p = debug_template.format(
                description=state["description"], code=code, error=output
            )
            logger.log(f"Iteration {iteration + 1}: Error encountered. Debugging...")
            logger.log(p)
            logger.log("==========\n\n\n\n")

            response, client = get_response(p, model=model, client=client, api_key=api_key)

            
            logger.log("Response received.")
            logger.log(response)
            logger.log("==========\n\n\n\n")

            code = extract_code(response)
            code_filename = f"code_{iteration + 1}.py"
            code_file_path = os.path.join(dir, code_filename)
            with open(code_file_path, "w") as f:
                f.write(code)
            logger.log(f"Iteration {iteration + 1}: Error encountered. Debugging...")
        iteration+=1
    else:
        logger.log("Max iterations reached with errors remaining.")
