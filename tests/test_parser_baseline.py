from __future__ import annotations

from ti_clang_linkinfo_analysis._xml_parser import LinkInfoXmlParser


def test_parse_counts_dpl_demo_debug(example_files) -> None:
    data = LinkInfoXmlParser(
        str(example_files["dpl_demo_debug"]), filter_debug=True
    ).parse()

    assert len(data.input_files) == 133
    assert len(data.object_components) == 1042
    assert len(data.logical_groups) == 39
    assert len(data.memory_areas) == 9
    assert len(data.filtered_component_ids) == 595

    no_input = [c for c in data.object_components.values() if c.input_file is None]
    assert len(no_input) == 11
    assert any(c.input_file is not None for c in data.object_components.values())


def test_parse_counts_enet_cli_debug(example_files) -> None:
    data = LinkInfoXmlParser(
        str(example_files["enet_cli_debug"]), filter_debug=True
    ).parse()

    assert len(data.input_files) == 401
    assert len(data.object_components) == 9427
    assert len(data.logical_groups) == 32
    assert len(data.memory_areas) == 5
    assert len(data.filtered_component_ids) == 2326

    no_input = [c for c in data.object_components.values() if c.input_file is None]
    assert len(no_input) == 68
    assert any(c.input_file is not None for c in data.object_components.values())
