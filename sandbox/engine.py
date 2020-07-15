import os
from collections import defaultdict
from io import StringIO

from insights import (
    apply_configs,
    apply_default_enabled,
    dr,
    load_default_plugins,
    load_packages,
)
from insights.core.archives import extract
from insights.core.hydration import create_context
from insights.formats._json import JsonFormat


class Engine:
    """
    Runs rules components from the configured packages. It returns a
    dictionary containing the formatted output along with timings and
    traceback data if requested.
    """

    def __init__(
        self,
        packages=None,
        Format=JsonFormat,
        include_timings=False,
        include_tracebacks=False,
        target_components=None,
        component_config=None,
    ):
        load_default_plugins()
        load_packages(packages or [])

        config = component_config or {}
        apply_default_enabled(config)
        apply_configs(config)
        target_components = [dr.get_component(c) for c in target_components or []]

        self._Format = Format
        self._include_timings = include_timings
        self._include_tracebacks = include_tracebacks
        self._target_components = target_components or None

    def process(self, path, broker=None):
        broker = dr.Broker() if broker is None else broker

        if os.path.isdir(path):
            results = {"results": self._evaluate(broker, path)}
        else:
            with extract(path) as extraction:
                results = {"results": self._evaluate(broker, extraction.tmp_dir)}

        if self._include_timings:
            results["timings"] = self._get_timings(broker)

        if self._include_tracebacks:
            results["tracebacks"] = self._get_tracebacks(broker)

        return results

    def _evaluate(self, broker, path):
        ctx = create_context(path)
        broker[ctx.__class__] = ctx

        output = StringIO()
        with self._Format(broker, stream=output):
            dr.run(self._target_components, broker=broker)
        output.seek(0)
        return output.read().encode("utf-8")

    def _get_timings(self, broker):
        return {dr.get_name(c): t for c, t in broker.exec_times.items()}

    def _get_tracebacks(self, broker):
        results = defaultdict(list)
        for c, es in broker.exceptions.items():
            name = dr.get_name(c)
            for e in es:
                results[name].append(broker.tracebacks[e])
        return dict(results)


class EngineAdapter:
    """
    Provides the setup and process methods used by the Controller.
    Digs options and data out of the raw dictionaries sent over the wire
    and delegates to the underlying Engine.
    """

    def __init__(self):
        self._engine = None

    def setup(self, config):
        self._engine = Engine(
            packages=config.get("packages", []),
            Format=dr.get_component(config["format"])
            if "format" in config
            else JsonFormat,
            include_timings=config.get("include_timings", False),
            include_tracebacks=config.get("include_tracebacks", False),
            target_components=config.get("target_components", []),
            component_config=config.get("component_config", {}),
        )

    def process(self, payload):
        broker = payload["broker"]
        path = payload["path"]
        return self._engine.process(path, broker=broker)
