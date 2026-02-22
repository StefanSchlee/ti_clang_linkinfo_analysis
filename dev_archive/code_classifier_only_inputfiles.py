import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List

import dotenv
from openai import OpenAI
from linkinfo_parser import LinkInfoParser, InputFile


# =========================
# Dataclasses
# =========================


@dataclass
class FeatureGroup:
    name: str
    description: str
    input_files: List[InputFile] = field(default_factory=list)

    def add(self, f: InputFile):
        self.input_files.append(f)


# =========================
# Classifier
# =========================


class InputFileFeatureGroupClassifier:
    def __init__(
        self,
        model: str,
        model_url: str,
        batch_size: int = 40,
        debug: bool = False,
    ):
        self.client = OpenAI(base_url=model_url)
        self.model = model
        self.batch_size = batch_size
        self.feature_groups: Dict[str, FeatureGroup] = {}

        # logging
        self.logger = logging.getLogger("InputFileFGClassifier")
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # ------------------------
    # Optional: load initial groups
    # ------------------------

    def load_initial_groups_from_file(self, path: str) -> None:
        with open(path, "r") as f:
            data = json.load(f)

        for fg in data.get("feature_groups", []):
            self.feature_groups[fg["name"]] = FeatureGroup(
                name=fg["name"],
                description=fg["description"],
            )

        self.logger.info(
            f"Loaded {len(self.feature_groups)} initial FeatureGroups from file"
        )

    # ------------------------
    # Main entry
    # ------------------------

    def build_feature_groups(self, input_files: Dict[str, InputFile]) -> None:
        files = list(input_files.values())

        for i in range(0, len(files), self.batch_size):
            batch = files[i : i + self.batch_size]
            self.logger.info(f"Processing batch {i} - {i + len(batch)}")
            self._process_batch(batch)

    # ------------------------
    # Batch logic
    # ------------------------

    def _process_batch(self, batch: List[InputFile]) -> None:
        batch_summary = [
            {
                "id": f.id,
                "name": f.name,
                "path": f.path,
            }
            for f in batch
        ]

        groups_summary = [
            {"name": fg.name, "description": fg.description}
            for fg in self.feature_groups.values()
        ]

        prompt = f"""
You are analyzing TI ARM linker input files to reconstruct the software architecture.

A FeatureGroup is a high-level architectural software component such as:
- OS / RTOS
- standard c/cpp libraries
- a driver library
- a middleware component
- a Third party library
- other major software component like parameter management, file system, networking stack, etc.


Each input file MUST belong to exactly ONE FeatureGroup.

Existing FeatureGroups:
{json.dumps(groups_summary, indent=2)}

New input files:
{json.dumps(batch_summary, indent=2)}

Tasks:
1) Assign each input_file_id to exactly one FeatureGroup.
2) Create new FeatureGroups if necessary.
3) Improve descriptions of existing groups if needed.

Return ONLY valid JSON in this format:

{{
  "updates": {{
    "modify_groups": [
        {{
            "name": "...", 
            "description": "..."
        }}
        # more modifications
    ],
    "new_groups": [
        {{
            "name": "...", 
            "description": "..."
        }}
        # more new groups]
  }},
  "assignments": [
    {{
        "input_file_id": "...", 
        "group_name": "..."
    }}
    # more assignments
  ]
}}
"""

        self.logger.debug("=== PROMPT ===")
        self.logger.debug(prompt)

        response = self._chat(prompt)

        self.logger.debug("=== RESPONSE ===")
        self.logger.debug(response)

        data = json.loads(response)

        # ---- update groups
        for mod in data["updates"].get("modify_groups", []):
            if mod["name"] in self.feature_groups:
                self.logger.debug(f"Updating group '{mod['name']}'")
                self.feature_groups[mod["name"]].description = mod["description"]

        for new in data["updates"].get("new_groups", []):
            if new["name"] not in self.feature_groups:
                self.logger.debug(f"Creating group '{new['name']}'")
                self.feature_groups[new["name"]] = FeatureGroup(
                    name=new["name"],
                    description=new["description"],
                )

        # ---- assignments
        id_map = {f.id: f for f in batch}

        # Create a map of assignments for quick lookup
        assignments_map = {}
        for assign in data["assignments"]:
            fid = assign["input_file_id"]
            group_name = assign["group_name"]
            assignments_map[fid] = group_name

        # Check that each input file in the batch has an assignment
        for f in batch:
            if f.id not in assignments_map:
                raise ValueError(
                    f"No assignment found for input file: {f.name or f.id}"
                )

            group_name = assignments_map[f.id]

            if group_name not in self.feature_groups:
                raise ValueError(
                    f"Unknown group '{group_name}' in assignment for {f.name or f.id}"
                )

            self.feature_groups[group_name].add(f)
            self.logger.debug(f"Assigned '{f.name}' -> {group_name}")

    # ------------------------
    # Helper
    # ------------------------

    def _chat(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content.strip()


# =========================
# Example usage
# =========================

if __name__ == "__main__":
    dotenv.load_dotenv("ollama.env")

    parser = LinkInfoParser(
        "example_files/dpl_demo_release_linkinfo.xml", filter_debug=True
    )
    parser.parse()

    classifier = InputFileFeatureGroupClassifier(
        model="gemma3:1b-it-qat",
        model_url="http://localhost:11434/v1",
        debug=True,
        batch_size=5,
    )

    # Optional:
    classifier.load_initial_groups_from_file("initial_feature_groups.json")

    classifier.build_feature_groups(parser.input_files)

    print("\nResult:\n")
    for fg in classifier.feature_groups.values():
        print(f"{fg.name}: {len(fg.input_files)} files")
