import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List
from openai import OpenAI
import dotenv
import os

# Dein Parser
from linkinfo_parser import LinkInfoParser, ObjectComponent, InputFile
import random


# =========================
# Dataclasses
# =========================


@dataclass
class FeatureGroup:
    name: str
    description: str
    object_components: List[ObjectComponent] = field(default_factory=list)

    def add(self, oc: ObjectComponent):
        self.object_components.append(oc)


# =========================
# LLM Classifier
# =========================


class FeatureGroupClassifier:
    def __init__(
        self,
        model_url: str,
        batch_size: int = 5,
        model: str = "gpt-4o-mini",
        debug: bool = False,
    ):
        self.client = OpenAI(base_url=model_url)
        self.model = model
        self.batch_size = batch_size
        self.feature_groups: Dict[str, FeatureGroup] = {}

        # Logging
        self.logger = logging.getLogger("FeatureGroupClassifier")
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # ------------------------
    # Phase 1: Initial Groups
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

    def create_initial_groups(self, input_files: Dict[str, InputFile]) -> None:
        files = list(input_files.values())

        for i in range(0, len(files), self.batch_size):
            batch = files[i : i + self.batch_size]
            self.logger.info(f"Phase 1: Processing input file batch {i}-{i+len(batch)}")
            self._process_inputfile_batch(batch)

    def _process_inputfile_batch(self, batch: List[InputFile]) -> None:
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
    You are building an architectural model of an embedded software based on linker input files.

    A FeatureGroup is a high-level architectural software component such as:
    - OS / RTOS
    - standard c/cpp libraries
    - a driver library
    - a middleware component
    - a Third party library
    - other major software component like parameter management, file system, networking stack, etc.

    Already found FeatureGroups (may be empty):
    {json.dumps(groups_summary, indent=2)}

    New input files to analyze:
    {json.dumps(batch_summary, indent=2)}

    Tasks:
    1. Analyze the input files and identify potential new FeatureGroups that are not yet in the existing list.

    Return JSON in this format:
    {{
        "new_groups": [
            {{
                "name": "...",
                "description": "..."
            }}
            # more new groups
        ]
    }}
    """

        self.logger.debug("=== PHASE 1 BATCH PROMPT ===")
        self.logger.debug(prompt)

        response = self._chat(prompt)

        self.logger.debug("=== PHASE 1 BATCH RESPONSE ===")
        self.logger.debug(response)

        data = json.loads(response)

        # Add new groups
        self.logger.debug(
            f"Adding {len(data.get('new_groups', []))} new FeatureGroups..."
        )
        for new in data.get("new_groups", []):
            if new["name"] not in self.feature_groups:
                self.logger.debug(f"Creating new group '{new['name']}'")
                self.feature_groups[new["name"]] = FeatureGroup(
                    name=new["name"],
                    description=new["description"],
                )

    # ------------------------
    # Phase 2: Classification
    # ------------------------

    def classify_components(self, components: Dict[str, ObjectComponent]) -> None:
        comps = list(components.values())

        for i in range(0, len(comps), self.batch_size):
            batch = comps[i : i + self.batch_size]
            self.logger.info(f"Classifying batch {i} - {i + len(batch)}")
            self._classify_batch(batch)

    def _classify_batch(self, batch: List[ObjectComponent]) -> None:
        batch_summary = []
        for oc in batch:
            batch_summary.append(
                {
                    "id": oc.id,
                    "name": oc.name,
                    "size": oc.size,
                    "input_file": oc.input_file.name if oc.input_file else None,
                    "path": oc.input_file.path if oc.input_file else None,
                    "readonly": oc.readonly,
                    "executable": oc.executable,
                }
            )

        groups_summary = [
            {"name": fg.name, "description": fg.description}
            for fg in self.feature_groups.values()
        ]

        prompt = f"""
You are classifying object components into software FeatureGroups.

Existing FeatureGroups:
{json.dumps(groups_summary, indent=2)}

Object components to classify:
{json.dumps(batch_summary, indent=2)}

Return JSON in this format:
{{
  "updates": {{
    "modify_groups": [{{"name": "...", "description": "..."}}],
    "new_groups": [{{"name": "...", "description": "..."}}]
  }},
  "assignments": [
    {{"object_component_id": "...", "group_name": "..."}}
  ]
}}
"""

        self.logger.debug("=== BATCH PROMPT ===")
        self.logger.debug(prompt)

        response = self._chat(prompt)

        self.logger.debug("=== BATCH RESPONSE ===")
        self.logger.debug(response)

        data = json.loads(response)

        # Update groups
        for mod in data["updates"].get("modify_groups", []):
            if mod["name"] in self.feature_groups:
                self.logger.debug(f"Updating description of group '{mod['name']}'")
                self.feature_groups[mod["name"]].description = mod["description"]

        for new in data["updates"].get("new_groups", []):
            if new["name"] not in self.feature_groups:
                self.logger.debug(f"Creating new group '{new['name']}'")
                self.feature_groups[new["name"]] = FeatureGroup(
                    name=new["name"],
                    description=new["description"],
                )

        # Assign components
        id_map = {oc.id: oc for oc in batch}

        for assign in data["assignments"]:
            oc_id = assign["object_component_id"]
            group_name = assign["group_name"]

            if group_name not in self.feature_groups or oc_id not in id_map:
                continue

            self.feature_groups[group_name].add(id_map[oc_id])
            self.logger.debug(f"Assigned OC '{oc_id}' to group '{group_name}'")

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

    classifier = FeatureGroupClassifier(
        model_url="http://localhost:11434/v1",
        model="gemma3:1b-it-qat",
        debug=True,
        batch_size=20,
    )

    print("Phase 1: Creating initial FeatureGroups...")
    classifier.load_initial_groups_from_file("initial_feature_groups.json")
    # classifier.create_initial_groups(parser.input_files)
    sample_keys = random.sample(
        list(parser.input_files.keys()), min(40, len(parser.input_files))
    )
    classifier.create_initial_groups({k: parser.input_files[k] for k in sample_keys})

    # print("Phase 2: Classifying ObjectComponents...")
    # classifier.classify_components(parser.object_components)

    # print("\nResult:\n")
    # for fg in classifier.feature_groups.values():
    #     total = sum(oc.size or 0 for oc in fg.object_components)
    #     print(f"{fg.name} ({total} bytes)")
