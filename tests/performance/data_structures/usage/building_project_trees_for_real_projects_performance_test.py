import argparse
import os

from typing import Dict

from src.data_structures.usage.build_project_prefix_tree_for_real_project import build_project_prefix_tree_for_local_java_project
from tests.performance.performance_test_framework import PerformanceTestFramework, run_performace_tests_for_class


class BuildingProjectTreesForRealProjectsPerformanceTest(PerformanceTestFramework):
    def __init__(self, project_locations_map: Dict[str, str], test_timeout_ms=20000):
        self._project_locations_map = project_locations_map
        super().__init__(test_timeout_ms)

    def test_build_project_tree_for_cassandra(self):
        cassandra_project_location = self._project_locations_map["cassandra"]
        build_project_prefix_tree_for_local_java_project(cassandra_project_location, ["src/java", "test/unit"])


def create_arg_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--test_timeout_ms", type=int, default=20_000)
    arg_parser.add_argument("--cassandra_location", type=str, default=f"{os.getenv("HOME")}/OpenSourceProjects/cassandra")
    return arg_parser


if __name__ == "__main__":
    arg_parser = create_arg_parser()
    args = arg_parser.parse_args()
    test_timeout_ms = args.test_timeout_ms
    project_locations_map = {
        "cassandra" : args.cassandra_location
    }
    run_performace_tests_for_class(
        BuildingProjectTreesForRealProjectsPerformanceTest, 
        test_timeout_ms=test_timeout_ms, project_locations_map=project_locations_map
    )
