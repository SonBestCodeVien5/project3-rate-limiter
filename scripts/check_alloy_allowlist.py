#!/usr/bin/env python3
"""Static contract check for Alloy's Docker discovery relabel rules."""

from pathlib import Path
import re
import unittest

CONFIG = Path(__file__).parents[1] / "deploy/monitoring/alloy/config.alloy"


class AlloyAllowlistTest(unittest.TestCase):
    def test_keep_rules_allow_only_fixed_and_opted_in_research_services(self):
        rules = re.findall(r"rule\s*\{(.*?)\n\s*\}", CONFIG.read_text(), re.S)
        keep_rules = []
        for rule in rules:
            attributes = re.findall(r"^\s*(\w+)\s*=", rule, re.M)
            self.assertEqual(len(attributes), len(set(attributes)), rule)
            if re.search(r'^\s*action\s*=\s*"keep"', rule, re.M):
                labels = re.search(r"source_labels\s*=\s*\[([^]]*)\]", rule).group(1)
                sources = re.findall(r'"([^"]+)"', labels)
                expression = re.search(r'regex\s*=\s*"([^"]+)"', rule).group(1)
                keep_rules.append((sources, re.compile(expression)))

        self.assertTrue(keep_rules)
        labels_by_source = {
            "__meta_docker_container_label_com_docker_compose_project": "project",
            "__meta_docker_container_label_com_docker_compose_service": "service",
            "__meta_docker_container_label_project3_monitoring_logs": "opt_in",
        }

        def accepted(project, service, opt_in=""):
            values = {"project": project, "service": service, "opt_in": opt_in}
            return all(pattern.fullmatch(";".join(values[labels_by_source[source]] for source in sources))
                       for sources, pattern in keep_rules)

        allowed = set()
        for project in ("project3-monitoring-demo", "project3-research-lab", "other"):
            for service in ("api1", "api2", "api3", "api4", "backend", "redis", "nginx", "prometheus", "grafana"):
                opt_ins = ("",) if project == "project3-monitoring-demo" else ("", "false", "true")
                if any(accepted(project, service, opt) for opt in opt_ins):
                    allowed.add((project, service))
        self.assertEqual(allowed, {
            ("project3-monitoring-demo", "api1"),
            ("project3-monitoring-demo", "api2"),
            ("project3-monitoring-demo", "backend"),
            *(("project3-research-lab", service) for service in ("api1", "api2", "api3", "api4", "backend")),
        })
        for service in ("api1", "api2", "api3", "api4", "backend"):
            self.assertFalse(accepted("project3-research-lab", service))
            self.assertFalse(accepted("project3-research-lab", service, "false"))
            self.assertTrue(accepted("project3-research-lab", service, "true"))
        self.assertFalse(accepted("other", "api1", "true"))
        for service in ("api3", "api4", "redis", "nginx"):
            self.assertFalse(accepted("project3-monitoring-demo", service))


if __name__ == "__main__":
    unittest.main()
