#!/usr/bin/env python
# coding: utf-8

import uvicorn
from typing import Optional
from fastapi import FastAPI, Path
from neo4j import GraphDatabase, basic_auth
from pydantic import BaseModel
from . import config as conf # import config from config.py

# Load contens from config.py file
uri = conf.uri
username = conf.username
password = conf.password

####################################################################
## Using python-dotenv as follows as alternative:
# import os
# from dotenv import load_dotenv, find_dotenv
# Load contents from .env file
# def find_load_dotenv():
#     return load_dotenv(find_dotenv())

# find_load_dotenv()

# uri: str = os.environ.get("NEO4J_AURA_URI")
# username: str = os.environ.get("NEO4J_AURA_USR")
# password: str = os.environ.get("NEO4J_AURA_PWD")
# auth: tuple[str, str] = (username, password)
####################################################################

# Initialize driver
driver = GraphDatabase.driver(uri, auth=basic_auth(username, password))

# Create class using BaseModel from pydantic \
# -> docs: https://pydantic-docs.helpmanual.io/usage/models/


class Neo4jNode(BaseModel):
    name: str
    emp_id: int


# Define FastAPI app
app = FastAPI(
    title="Rob's REST API Assignment",
    description="REST API built for Neo4j with FastAPI & Neo4j",
    version=0.1,
    docs_url="/docs",
    redoc_url="/redoc",
)

# GET Request: Landing Page \
# - http://127.0.0.1:8000/ or http://127.0.0.1:8000/get-all-nodes/home


@app.get("/")
def home():
    return {"Response": "Rob Piombino's FastAPI REST API"}


# GET request: Fetch all nodes and display results \
# - http://127.0.0.1:8000/get-all-nodes
@app.get(
    "/get-all-nodes",
    summary="Return all Employee nodes to client as JSON object",
    description="Retrieve all Employee Nodes from Neo4j",
)
async def get_all_nodes() -> dict:
    with driver.session() as session:
        cyp: str = (
            "MATCH (employee:Employee) "
            "RETURN employee.name AS name, employee.emp_id AS emp_id;"
        )
        result: dict = session.run(query=cyp).data()
    return result


# GET request -> Fetch node by emp_id property \
# - http://127.0.0.1:8000/get-node-by-id/{emp_id}
@app.get("/get-node-by-id/{emp_id}")
async def get_node_by_id(
    emp_id: Optional[int] = Path(
        None,
        description="The employee's AND/OR candidate employee's employee ID at Neo4j Inc.",
    )
) -> dict:
    with driver.session() as session:
        cyp = (
            "MATCH (employee:Employee {emp_id:$emp_id} ) "
            "RETURN employee.name AS name, employee.emp_id AS emp_id;"
        )
        params_dict: dict = {"name": "name", "emp_id": emp_id}
        result: dict = session.run(cyp, params_dict).data()
    return result


# GET request -> Fetch node by name property \
# -> http://127.0.0.1:8000/get-node-by-name/{name}
@app.get("/get-node-by-name/{name}")
async def get_node_by_name(
    *,
    name: Optional[str] = Path(
        None,
        description="The employee's AND/OR candidate employee's name at Neo4j Inc.",
    ),
) -> dict:
    with driver.session() as session:
        cyp = (
            "MATCH (employee:Employee {name:$name} ) "
            "RETURN employee.name AS name, employee.emp_id AS emp_id;"
        )
        params_dict: dict = {"name": name, "emp_id": "emp_id"}
        result: dict = session.run(cyp, params_dict).data()
    return result


# GET Request -> Fetch node by name property (fuzzy matching via CONTAINS operation) - http://127.0.0.1:8000/search/{search_term}
@app.get("/search")
async def get_search(search_term: str = None) -> dict:
    def work(tx, q_):
        result = tx.run(
            "MATCH (employee:Employee) WHERE toLower(employee.name) CONTAINS toLower($name) RETURN employee",
            {"name": q_},
        )

        return [record["employee"] for record in result]

    if search_term is None:
        return []
    with driver.session() as session:
        result = session.read_transaction(work, search_term)
        return list(result)


# POST Request sent to Neo4j to create an Employee Node with name & emp_id node properties
@app.post("/create-node")
async def create_node(neo4j_node: Neo4jNode) -> dict:
    with driver.session() as session:
        cyp: str = (
            "CREATE (employee:Employee {name:$name,emp_id:$emp_id} ) "
            "RETURN employee.name AS name, employee.emp_id as emp_id;"
        )
        params_dict: dict = {"name": neo4j_node.name, "emp_id": neo4j_node.emp_id}
        session = driver.session()
        result: dict = session.run(cyp, params_dict).data()
    return result


if __name__ == "__main__":
    uvicorn.run(app="app.main:app", host="0.0.0.0", port=8000, reload=True)
