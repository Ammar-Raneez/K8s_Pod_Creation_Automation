"""
This module is a simple draft FastAPI for demonstration
"""

import os
from typing import Any, Dict, Tuple

import pyodbc
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_master_db_connection() -> pyodbc.Connection:
    """
    Establish a connection to the master database

    :return: A Connection object that represents the database
    :rtype: pyodbc.Connection
    """

    return pyodbc.connect(os.getenv("MASTER_CONNECTION_STRING"))


def get_container_db_connection() -> MongoClient:
    """
    Establishes a connection to MongoDB Atlas

    :return: A client object that represents the database
    :rtype: MongoClient
    """

    return MongoClient(os.getenv("ATLAS_CONNECTION_STRING"))


def get_container_info() -> Dict[str, str | None]:
    """
    Parse and return all container information

    :return: Container information dictionary
    :rtype: Dict[str, str]
    """

    return {
        "name": os.getenv("CONTAINER_NAME"),
        "label": os.getenv("CONTAINER_LABEL"),
    }


def create_dashboard_info(
    container_info: Dict[str, str]
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Create and return a draft Grafana dashboard template with authentication headers

    :return: The dashboard template and authentication headers
    :rtype: Tuple[Dict[str, Any], Dict[str, str]]
    """

    GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY")

    dashboard_template = {
        "dashboard": {
            "id": None,
            "title": f'{container_info["name"]} Dashboard',
            "tags": [container_info["label"]],
            "timezone": "browser",
            "panels": [
                {
                    "type": "graph",
                    "title": "Container Metrics",
                    "gridPos": {"x": 0, "y": 0, "w": 24, "h": 8},
                    "targets": [],
                }
            ],
            "schemaVersion": 30,
            "version": 1,
        },
        "overwrite": True,
    }

    headers = {
        "Authorization": f"Bearer {GRAFANA_API_KEY}",
        "Content-Type": "application/json",
    }

    return dashboard_template, headers


def update_master_source(dashboard_url: str):
    """
    Updates Master DB with new container details

    :param dashboard_url: The created dashboard's ID
    :type dashboard_url: str
    """

    master_conn = get_master_db_connection()
    cursor = master_conn.cursor()
    container_info = get_container_info()

    container_check = "SELECT CASE WHEN EXISTS (SELECT 1 FROM [dbo].[Master] WHERE containerLabel = ?) THEN 1 ELSE 0 END;"
    cursor.execute(container_check, container_info["label"])
    container_exists = cursor.fetchone()[0]

    if not container_exists:
        table_name = "Master"
        columns = [
            "dashboardURL",
            "containerLabel",
            "containerName",
        ]
        values = [
            dashboard_url,
            container_info["label"],
            container_info["name"],
        ]
        placeholders = ",".join(["?"] * len(columns))

        cursor.execute(
            f'INSERT INTO {table_name} ({",".join(columns)}) values ({placeholders})',
            values,
        )

    master_conn.commit()
    cursor.close()


def create_grafana_dashboard(container_info: Dict[str, str]) -> str:
    """
    Create a new Grafana dashboard for the specific container

    :param container_info: Dictionary containing container details
    :type container_info: Dict[str, str]

    :return: The created dashboard's ID
    :rtype: str
    """

    GRAFANA_URL = os.getenv("GRAFANA_URL")
    dashboard_template, headers = create_dashboard_info(container_info)

    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db", json=dashboard_template, headers=headers
    )

    if response.status_code == 200:
        print(f'Dashboard for container {container_info["name"]} created successfully')
        dashboard_url = response.json()["url"]
        return dashboard_url
    else:
        print(f"Failed to create dashboard: {response.text}")


def update_shared_source(container_info: Dict[str, str], dashboard_url: str):
    """
    Updates shared MongoDB with container data streams

    :param container_info: Dictionary containing container details
    :type container_info: Dict[str, str]
    """

    client = get_container_db_connection()
    container_db = client[container_info["label"]]
    data = container_db["data"]
    data.insert_one({"name": container_info["name"], "dashboardURL": dashboard_url})


@app.on_event("startup")
def init():
    """
    Update Master and Shared data sources
    """

    container_info = get_container_info()
    dashboard_url = create_grafana_dashboard(container_info)
    update_shared_source(container_info, dashboard_url)
    update_master_source(dashboard_url)


@app.get(f'/api/{os.getenv("CONTAINER_LABEL")}/details', response_model=Dict[str, str])
def get_details() -> Dict[str, str]:
    """
    Get created container details

    :return: The created container's name
    :rtype: Dict[str,str]
    """

    container_info = get_container_info()
    client = get_container_db_connection()

    # Create a database of name equal to the container label
    container_db = client[container_info["label"]]

    return {
        "Container name": container_info["name"],
        "Container DB": f"Successfully connected to {container_db}",
    }
