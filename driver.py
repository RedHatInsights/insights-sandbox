#!/usr/bin/env python3
"""
This script is only for testing the sandbox.
"""
import argparse

from insights import dr, parse_plugins
from insights_sandbox.client import Client


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--plugins", "-p", help="plugins to load", default="")
    p.add_argument("archive", help="pass an archive to analyze.")
    return p.parse_args()


def main():
    args = parse_args()
    broker = dr.Broker()
    packages = parse_plugins(args.plugins)
    with Client(packages=packages) as client:
        doc = client.process(args.archive, broker=broker)
        print(doc["results"].decode("utf-8"))


if __name__ == "__main__":
    main()
