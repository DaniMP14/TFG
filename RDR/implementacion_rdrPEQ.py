import mysql.connector
import getpass
import pandas as pd

def load_concepts():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password = getpass.getpass("Introduce la contraseña de MySQL: "),
        database="tfg_nanotech",
        charset="utf8mb4"
    )
    query = "SELECT code, display_name, definition, synonyms, parents, concept_subset FROM thesaurus_concepts"
    df = pd.read_sql(query, conn)
    conn.close()
    return df


class RDRRule:
    def __init__(self, name, condition, action):
        self.name = name
        self.condition = condition     # función: input → bool
        self.action = action           # función: input → output CALLABLE
        self.exceptions = []

    def evaluate(self, input_case):
        if self.condition(input_case):
            for ex in self.exceptions:
                result = ex.evaluate(input_case)
                if result is not None:
                    return result
            return self.action(input_case)
        return None

    def add_exception(self, rule):
        self.exceptions.append(rule)