from pathlib import Path

from TestSuite.json_based import JSONBased


class IncidentField(JSONBased):
    def __init__(
        self, name: str, incident_field_dir_path: Path, json_content: dict = None
    ):
        self.incident_field_file_path = incident_field_dir_path / f"{name}.json"
        super().__init__(
            dir_path=incident_field_dir_path,
            name=name,
            prefix="incidentfield",
            json_content=json_content,
        )

    def create_default(self):
        self.write_json(
            {
                "id": self.id,
                "description": "test description",
                "cliName": self.id.lower(),
                "name": self.id,
                "associatedToAll": False,
                "type": "shortText",
                "associatedTypes": [],
                "threshold": 72,
                "fromVersion": "6.10.0",
            }
        )
