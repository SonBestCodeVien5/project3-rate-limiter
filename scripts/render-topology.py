#!/usr/bin/env python3
"""Render an isolated 1/2/4 API Compose lab from Docker Compose's resolved JSON."""

import argparse
import copy
import json
from pathlib import Path
import re
import sys


def render(base, instances, output, host_port, fresh_state=False):
    if instances not in (1, 2, 4):
        raise ValueError("instances must be 1, 2, or 4")
    if not 1024 <= host_port <= 65535:
        raise ValueError("host port must be between 1024 and 65535")
    services = base.get("services", {})
    if not {"api1", "api2", "backend", "redis", "nginx"} <= services.keys():
        raise ValueError("resolved Compose config is missing a baseline service")
    api_template = services["api1"]
    if not isinstance(api_template.get("environment"), dict):
        raise ValueError("resolved API environment must be an object")
    config = copy.deepcopy(base)
    config["name"] = "project3-research-lab"
    config["services"] = {name: service for name, service in config["services"].items()
                          if not re.fullmatch(r"api[0-9]+", name)}
    for name in ("backend", "redis"):
        config["services"][name].pop("ports", None)
    for number in range(1, instances + 1):
        api = copy.deepcopy(api_template)
        api["environment"]["INSTANCE_ID"] = f"api-{number}"
        api.pop("ports", None)
        config["services"][f"api{number}"] = api
    nginx = config["services"]["nginx"]
    nginx["ports"] = [{"mode": "ingress", "target": 8080, "published": str(host_port),
                       "protocol": "tcp", "host_ip": "127.0.0.1"}]
    nginx["depends_on"] = {f"api{number}": {"condition": "service_healthy", "required": True}
                            for number in range(1, instances + 1)}
    nginx["volumes"] = [{"type": "bind", "source": str(output / "nginx.conf"),
                         "target": "/etc/nginx/nginx.conf", "read_only": True,
                         "bind": {"create_host_path": False}}]
    upstream = "\n".join(f"        server api{number}:8080;" for number in range(1, instances + 1))
    nginx_config = ("events { worker_connections 2048; }\nhttp {\n    access_log off;\n"
                    f"    upstream api {{\n{upstream}\n        keepalive 64;\n    }}\n"
                    "    server {\n        listen 8080;\n        location / {\n"
                    "            proxy_pass http://api;\n            proxy_http_version 1.1;\n"
                    "            proxy_set_header Connection \"\";\n"
                    "            proxy_next_upstream off;\n"
                    "            proxy_connect_timeout 1s;\n"
                    "            proxy_read_timeout 10s;\n        }\n    }\n}\n")
    env = config["services"]["api1"]["environment"]
    required = ("MODE", "ALGORITHM", "FAIL_POLICY", "NAMESPACE", "LIMIT", "WINDOW", "CAPACITY", "RATE")
    if any(key not in env for key in required):
        raise ValueError("resolved API environment lacks a policy field")
    window = str(env["WINDOW"])
    match = re.fullmatch(r"([0-9]+)(ns|us|ms|s|m|h)", window)
    if not match:
        raise ValueError("WINDOW must be one positive Go duration unit")
    factor = {"ns": 1e-6, "us": 1e-3, "ms": 1, "s": 1000, "m": 60000, "h": 3600000}[match[2]]
    window_ms = int(int(match[1]) * factor)
    if window_ms <= 0:
        raise ValueError("WINDOW must be at least 1ms for the analysis policy")
    policy = {"schema_version": 1, "mode": str(env["MODE"]),
              "algorithm": str(env["ALGORITHM"]), "fail_policy": str(env["FAIL_POLICY"]),
              "namespace": str(env["NAMESPACE"]), "limit": int(env["LIMIT"]),
              "window_ms": window_ms, "capacity": int(env["CAPACITY"]),
              "rate_per_sec": float(env["RATE"]), "state_reset": fresh_state}
    if policy["mode"] not in ("none", "local", "redis") or policy["algorithm"] not in ("fixed-window", "token-bucket") or policy["fail_policy"] not in ("open", "closed") or not policy["namespace"]:
        raise ValueError("resolved API policy contains invalid values")
    return config, nginx_config, policy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-config", required=True, type=Path,
                        help="JSON from docker compose config --format json")
    parser.add_argument("--output", required=True, type=Path, help="new output directory")
    parser.add_argument("--instances", required=True, type=int, choices=(1, 2, 4))
    parser.add_argument("--host-port", type=int, default=18080)
    parser.add_argument("--fresh-state", action="store_true",
                        help="assert that the caller creates fresh containers and a new namespace")
    args = parser.parse_args()
    try:
        output = args.output.resolve()
        if output.exists():
            raise ValueError(f"output already exists: {output}")
        base = json.loads(args.base_config.read_text())
        config, nginx, policy = render(base, args.instances, output, args.host_port, args.fresh_state)
        output.mkdir(parents=True, exist_ok=False)
        (output / "compose.json").write_text(json.dumps(config, indent=2) + "\n")
        (output / "nginx.conf").write_text(nginx)
        (output / "policy.json").write_text(json.dumps(policy, indent=2) + "\n")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f"render-topology: {exc}\n")


if __name__ == "__main__":
    main()
