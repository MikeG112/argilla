#  Copyright 2021-present, the Recognai S.L. team.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from datetime import datetime
from uuid import UUID

from argilla._constants import API_KEY_HEADER_NAME
from argilla.server.models import Dataset
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import (
    AnnotatorFactory,
    DatasetFactory,
    WorkspaceFactory,
    WorkspaceUserFactory,
)


def test_list_datasets(client: TestClient, admin_auth_header: dict):
    dataset_a = DatasetFactory.create(name="dataset-a")
    dataset_b = DatasetFactory.create(name="dataset-b", guidelines="guidelines")
    dataset_c = DatasetFactory.create(name="dataset-c")

    response = client.get("/api/v1/datasets", headers=admin_auth_header)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(dataset_a.id),
            "name": "dataset-a",
            "guidelines": None,
            "workspace_id": str(dataset_a.workspace_id),
            "inserted_at": dataset_a.inserted_at.isoformat(),
            "updated_at": dataset_a.updated_at.isoformat(),
        },
        {
            "id": str(dataset_b.id),
            "name": "dataset-b",
            "guidelines": "guidelines",
            "workspace_id": str(dataset_b.workspace_id),
            "inserted_at": dataset_b.inserted_at.isoformat(),
            "updated_at": dataset_b.updated_at.isoformat(),
        },
        {
            "id": str(dataset_c.id),
            "name": "dataset-c",
            "guidelines": None,
            "workspace_id": str(dataset_c.workspace_id),
            "inserted_at": dataset_c.inserted_at.isoformat(),
            "updated_at": dataset_c.updated_at.isoformat(),
        },
    ]


def test_list_datasets_without_authentication(client: TestClient):
    response = client.get("/api/v1/datasets")

    assert response.status_code == 401


def test_list_datasets_as_annotator(client: TestClient, db: Session):
    annotator = AnnotatorFactory.create()
    workspace = WorkspaceFactory.create()
    WorkspaceUserFactory.create(workspace_id=workspace.id, user_id=annotator.id)

    DatasetFactory.create(name="dataset-a", workspace=workspace)
    DatasetFactory.create(name="dataset-b", workspace=workspace)
    DatasetFactory.create(name="dataset-c")

    response = client.get("/api/v1/datasets", headers={API_KEY_HEADER_NAME: annotator.api_key})

    assert response.status_code == 200
    assert [dataset["name"] for dataset in response.json()] == ["dataset-a", "dataset-b"]


def test_create_dataset(client: TestClient, db: Session, admin_auth_header: dict):
    workspace = WorkspaceFactory.create()
    dataset_json = {"name": "name", "guidelines": "guidelines", "workspace_id": str(workspace.id)}

    response = client.post("/api/v1/datasets", headers=admin_auth_header, json=dataset_json)

    assert response.status_code == 200
    assert db.query(Dataset).count() == 1

    response_body = response.json()
    assert db.get(Dataset, UUID(response_body["id"]))
    assert response_body == {
        "id": str(UUID(response_body["id"])),
        "name": "name",
        "guidelines": "guidelines",
        "workspace_id": str(workspace.id),
        "inserted_at": datetime.fromisoformat(response_body["inserted_at"]).isoformat(),
        "updated_at": datetime.fromisoformat(response_body["updated_at"]).isoformat(),
    }


def test_create_dataset_without_authentication(client: TestClient, db: Session):
    dataset_json = {"name": "name", "workspace_id": str(WorkspaceFactory.create().id)}

    response = client.post("/api/v1/datasets", json=dataset_json)

    assert response.status_code == 401
    assert db.query(Dataset).count() == 0


def test_create_dataset_as_annotator(client: TestClient, db: Session):
    annotator = AnnotatorFactory.create()
    dataset_json = {"name": "name", "workspace_id": str(WorkspaceFactory.create().id)}

    response = client.post("/api/v1/datasets", headers={API_KEY_HEADER_NAME: annotator.api_key}, json=dataset_json)

    assert response.status_code == 403
    assert db.query(Dataset).count() == 0


def test_create_dataset_with_existent_name(client: TestClient, db: Session, admin_auth_header: dict):
    dataset = DatasetFactory.create(name="name")
    dataset_json = {"name": "name", "workspace_id": str(dataset.workspace_id)}

    response = client.post("/api/v1/datasets", headers=admin_auth_header, json=dataset_json)

    assert response.status_code == 409
    assert db.query(Dataset).count() == 1
