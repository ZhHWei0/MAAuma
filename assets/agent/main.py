"""MaaUma's stateful daily race action; screen operations remain in pipeline JSON."""

import json
import logging
import re
import sys
import time
import unicodedata
from pathlib import Path

# Import the agent package before any classes that initialize MaaFramework.
from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction

# Import registers the legendary race action on the same AgentServer.
import daily_legend


LOG = logging.getLogger("maauma.daily_race")


def read_number(context: Context, node: str):
    """Return one numeric OCR result and its current, normalized screen box."""
    job = context.tasker.controller.post_screencap().wait()
    if not job.succeeded or context.tasker.stopping:
        return None
    detail = context.run_recognition(node, job.get())
    if not detail or not detail.hit:
        LOG.warning("No number recognized in %s", node)
        return None

    candidates = []
    for result in detail.filtered_results:
        text = unicodedata.normalize("NFKC", result.text)
        digits = re.sub(r"[\s,]", "", text)
        if re.fullmatch(r"[0-9]+", digits):
            candidates.append((int(digits), tuple(result.box)))
    if len(candidates) != 1:
        LOG.warning("Expected one number; found %s: %s", len(candidates), candidates)
        return None
    return candidates[0]


def active(context: Context, deadline: float) -> bool:
    return not context.tasker.stopping and time.monotonic() < deadline


@AgentServer.custom_action("DailyRaceSelectStableNumber")
class DailyRaceSelectStableNumber(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            params = json.loads(argv.custom_action_param)
            deadline = time.monotonic() + params["timeout_ms"] / 1000
            previous = None
            while active(context, deadline):
                current = read_number(context, params["ocr_node"])
                # A slow screenshot/OCR must never cause a click after timeout.
                if not active(context, deadline):
                    break
                if current is None:
                    # Missing/ambiguous OCR is not an unchanged number. Reset
                    # the baseline so comparison always spans a valid swipe.
                    previous = None
                    time.sleep(min(0.1, max(0, deadline - time.monotonic())))
                    continue

                number, _ = current
                LOG.info("Number before swipe: %s; current: %s", previous, number)
                if previous is not None and number == previous:
                    result = context.run_action(params["click_node"])
                    LOG.info("Stable number %s; fixed-position selection success: %s", number, bool(result and result.success))
                    return bool(result and result.success)

                previous = number
                # This JSON helper performs ONE 1000 ms swipe, then waits
                # 1000 ms. All three initial swipes happen before this action.
                result = context.run_action(params["swipe_node"])
                if not result or not result.success:
                    LOG.error("Comparison swipe failed")
                    return False

            LOG.error("Number comparison stopped or exceeded %s ms", params["timeout_ms"])
            return False
        except Exception:
            LOG.exception("Daily race number comparison failed")
            return False


def main() -> None:
    Path("debug").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler("debug/maauma-agent.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    if len(sys.argv) < 2:
        raise SystemExit("This agent is started by MFA with its socket identifier.")
    if not AgentServer.start_up(sys.argv[-1]):
        raise SystemExit("Failed to start MaaUma AgentServer.")
    try:
        AgentServer.join()
    finally:
        AgentServer.shut_down()


if __name__ == "__main__":
    main()
