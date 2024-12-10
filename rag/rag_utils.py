import os
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum
load_dotenv()


# Explicitly set the root path to the project directory
root_path = Path("/home/ekats/scratch/OptiMUS-main")

# Ensure the root path exists
if not root_path.exists():
    raise FileNotFoundError(f"Specified root_path does not exist: {root_path}")

logs_path = root_path / "test"
data_path = root_path / "data"
rag_path = data_path / "rag"
rag_path.mkdir(exist_ok=True, parents=True)
constraint_path = rag_path/"constraints.pkl"
problem_descriptions_vector_db_path = rag_path / "problem_descriptions_vector.db"
constraint_vector_db_path = rag_path / "constraint_vector.db"
objective_descriptions_vector_db_path = rag_path / "objective_descriptions_vector.db"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class RAGMode(Enum):
    PROBLEM_DESCRIPTION = "problem_description"
    CONSTRAINT_OR_OBJECTIVE = "constraint_or_objective"
    PROBLEM_LABELS = "problem_labels"

    def __str__(self):
        return self.value
