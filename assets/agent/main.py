"""MaaUma stateful actions; screen operations remain in pipeline JSON."""

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
    return read_number_from_frame(context, node, job.get())


def read_number_from_frame(context: Context, node: str, image):
    detail = context.run_recognition(node, image)
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


@AgentServer.custom_action("RewardDerbySpin")
class RewardDerbySpin(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            params = json.loads(argv.custom_action_param)
            interval = params["interval_ms"] / 1000
            stage_timeout = params["stage_timeout_ms"] / 1000
            deadline = time.monotonic() + stage_timeout
            spin_node = params["spin_node"]
            close_node = params["close_node"]
            insufficient_node = params["insufficient_node"]
            spin_point = None
            probe_attempts = 0
            after_result = False
            log = logging.getLogger("maauma.reward_derby")

            def running():
                return active(context, deadline)

            def click(node, box):
                nonlocal tick
                if not running():
                    return False
                tick = time.monotonic()
                result = context.run_action(node, box=box)
                return bool(result and result.success)

            while running():
                tick = time.monotonic()
                frame_job = context.tasker.controller.post_screencap().wait()
                if not frame_job.succeeded or not running():
                    return False
                frame = frame_job.get()
                insufficient = context.run_recognition(insufficient_node, frame)
                if not running():
                    return False
                if insufficient and insufficient.hit:
                    log.info("Game reported insufficient derby coins; finished")
                    return True

                close = context.run_recognition(close_node, frame) if spin_point is not None or after_result else None
                if close and close.hit:
                    if not click(close_node, tuple(close.box)):
                        return False
                    if spin_point is not None:
                        log.info("Closed derby result; waiting for spin prompt before reading balance")
                        deadline = time.monotonic() + stage_timeout
                    spin_point = None
                    probe_attempts = 0
                    after_result = True
                else:
                    prompt = context.run_recognition(spin_node, frame)
                    if prompt and prompt.hit:
                        # Read the current balance each time the button is ready.
                        # An earlier OCR result cannot authorize another spin.
                        balance = read_number_from_frame(context, params["balance_node"], frame)
                        if not running():
                            return False
                        coins = balance[0] if balance is not None else None
                        if coins is not None and coins < params["cost"]:
                            log.info("Derby balance %s is below %s; finished", coins, params["cost"])
                            return True
                        if coins is None and probe_attempts >= 3:
                            log.info("Unreadable balance and unchanged spin prompt after %d attempts; finished", probe_attempts)
                            return True
                        if spin_point is None:
                            x, y, width, height = prompt.box
                            spin_point = (x + width // 2, y + height // 2, 1, 1)
                            log.info("Derby balance=%s; clicking at %s", coins, spin_point[:2])
                            deadline = time.monotonic() + stage_timeout
                            after_result = False
                        probe_attempts = probe_attempts + 1 if coins is None else 0
                    else:
                        # During the animation, keep pressing the same point to skip it.
                        probe_attempts = 0
                    if spin_point is not None and not click(spin_node, spin_point):
                        return False

                # Keep presses at least one interval apart and stay responsive to Stop.
                next_tick = tick + interval
                while running() and (remaining := next_tick - time.monotonic()) > 0:
                    time.sleep(min(0.1, remaining))

            log.warning("Derby stopped or no progress for %s ms", params["stage_timeout_ms"])
            return False
        except Exception:
            logging.getLogger("maauma.reward_derby").exception("Derby spin failed")
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
