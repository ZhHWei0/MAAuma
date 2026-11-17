"""Select by a strong avatar match; use card text to confirm weaker matches."""

import json
import logging
import time
import unicodedata
from pathlib import Path

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


LOG = logging.getLogger("maauma.daily_legend")
CATALOG_PATH = Path(__file__).with_name("daily_legend_characters.json")


def wait_while_running(seconds, running):
    end = time.monotonic() + seconds
    while running():
        remaining = end - time.monotonic()
        if remaining <= 0:
            return True
        time.sleep(min(0.1, remaining))
    return False


def compact(text):
    # Normalize full-width punctuation and whitespace, retaining 春 / 秋.
    return "".join(c for c in unicodedata.normalize("NFKC", text) if c.isalnum())


def race_filter_from_text(readings):
    text = "".join(compact(value) for value in readings)
    distances = [value for value in ("短距离", "长距离", "英里", "中距离") if value in text]
    return distances[0] if len(distances) == 1 else None


@AgentServer.custom_action("DailyLegendConfigureRaceFilter")
class DailyLegendConfigureRaceFilter(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            params = json.loads(argv.custom_action_param)
            deadline = time.monotonic() + params["timeout_ms"] / 1000

            def running():
                return not context.tasker.stopping and time.monotonic() < deadline

            while running():
                job = context.tasker.controller.post_screencap().wait()
                if not job.succeeded or not running():
                    return False
                image = job.get()
                for only_rec in (False, True):
                    if not running():
                        return False
                    detail = context.run_recognition(params["ocr_node"], image, {
                        params["ocr_node"]: {"recognition": {"type": "OCR", "param": {
                            "expected": [], "only_rec": only_rec, "order_by": "Horizontal",
                        }}}
                    })
                    readings = [result.text for result in detail.filtered_results] if detail and detail.hit else []
                    race_filter = race_filter_from_text(readings)
                    LOG.info("Legend race type: readings=%s filter=%s only_rec=%s", readings, race_filter, only_rec)
                    if not running():
                        return False
                    if race_filter:
                        expected = "\\s*".join(race_filter)
                        return context.override_pipeline({params["filter_node"]: {
                            "recognition": {"type": "OCR", "param": {"expected": [expected]}},
                        }})
                if not wait_while_running(0.5, running):
                    break
            LOG.error("Legend race type missing or ambiguous; entry was not clicked")
            return False
        except Exception:
            LOG.exception("Legend race type configuration failed")
            return False


def relative_roi(box, offset, bounds):
    x, y = box[:2]
    dx, dy, width, height = offset
    roi = [x + dx, y + dy, width, height]
    bx, by, bw, bh = bounds
    # Partially visible cards must scroll fully into view before validation.
    if roi[0] < bx or roi[1] < by or roi[0] + width > bx + bw or roi[1] + height > by + bh:
        return None
    return roi


def read_card_text(context, image, node, roi, target, running):
    """Join OCR fragments so an artistic name split over two lines can match."""
    target = compact(target)
    for only_rec in (False, True):
        if not running():
            return False
        detail = context.run_recognition(node, image, {
            node: {"recognition": {"type": "OCR", "param": {
                "roi": roi, "expected": [], "only_rec": only_rec, "order_by": "Vertical",
            }}}
        })
        if not detail:
            LOG.warning("OCR did not start: node=%s roi=%s", node, roi)
            continue
        LOG.info("OCR raw node=%s roi=%s only_rec=%s hit=%s results=%s", node, roi, only_rec, detail.hit,
                 [(r.text, round(r.score, 3)) for r in detail.all_results])
        if not detail.hit:
            continue
        results = detail.filtered_results
        # OCR can return one box, several characters, or two separate lines.
        vertical = sorted(results, key=lambda r: (r.box[1], r.box[0]))
        horizontal = sorted(results, key=lambda r: (r.box[0], r.box[1]))
        readings = [r.text for r in results]
        readings += ["".join(r.text for r in vertical), "".join(r.text for r in horizontal)]
        LOG.info("Text check node=%s roi=%s expected=%s readings=%s", node, roi, target, readings)
        if any(target in compact(text) for text in readings):
            return True
    return False


def verify_card_field(context, image, node, roi, target, template, running):
    if read_card_text(context, image, node, roi, target, running):
        return True
    if not template or not running():
        LOG.warning("Card text rejected: node=%s expected=%s roi=%s", node, target, roi)
        return False
    # Some artistic names are unreadable to OCR; try the same text as an image.
    image_path = Path(__file__).parent.parent / "resource" / "image" / template
    if not image_path.is_file():
        LOG.error("Missing text template: %s", image_path)
        return False
    template_node = "日常传奇赛事_文字图片校验"
    detail = context.run_recognition(template_node, image, {
        template_node: {"recognition": {"type": "TemplateMatch", "param": {
            "roi": roi, "template": [template],
        }}}
    })
    LOG.info("Text image check expected=%s template=%s roi=%s hit=%s candidates=%s", target, template, roi,
             bool(detail and detail.hit),
             [(round(r.score, 3), tuple(r.box)) for r in detail.all_results] if detail else [])
    return bool(detail and detail.hit)


@AgentServer.custom_action("DailyLegendSelectCard")
class DailyLegendSelectCard(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            params = json.loads(argv.custom_action_param)
            catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
            character = next((c for c in catalog["characters"] if c["name"] == params["character"]), None)
            if character is None:
                LOG.error("Unknown dropdown character: %s", params["character"])
                return False
            LOG.info("Selected character=%s source=dropdown", character["name"])
            template = character["avatar_template"]
            image_path = Path(__file__).parent.parent / "resource" / "image" / template
            if not image_path.is_file():
                LOG.error("Missing avatar template: %s", image_path)
                return False

            deadline = time.monotonic() + params["timeout_ms"] / 1000

            def running():
                return not context.tasker.stopping and time.monotonic() < deadline

            bounds = catalog["list_roi"]
            avatar_threshold = catalog["avatar_threshold"]
            direct_click_threshold = catalog["avatar_direct_click_threshold"]
            if not 0 <= avatar_threshold <= direct_click_threshold <= 1:
                LOG.error("Invalid avatar thresholds: %s / %s", avatar_threshold, direct_click_threshold)
                return False
            # Initial reset and its 1-second wait finish in the pipeline
            # before entering this callback. Only searching uses this deadline.
            page = 0
            swipe_node = params["swipe_node"]
            while running():
                job = context.tasker.controller.post_screencap().wait()
                if not job.succeeded or not running():
                    return False
                image = job.get()
                detail = context.run_recognition(params["avatar_node"], image, {
                    params["avatar_node"]: {"recognition": {"type": "TemplateMatch", "param": {
                        "roi": bounds, "template": [template], "green_mask": True,
                        "threshold": avatar_threshold,
                    }}}
                })
                if detail and detail.hit:
                    # A false positive at the highest score must not hide a
                    # lower-scoring candidate whose card text is correct.
                    for candidate in sorted(detail.filtered_results, key=lambda r: r.score, reverse=True):
                        if not running():
                            return False
                        box = tuple(candidate.box)
                        LOG.info("Avatar candidate character=%s page=%s score=%.3f box=%s", character["name"], page, candidate.score, box)
                        if candidate.score < avatar_threshold:
                            continue
                        if candidate.score >= direct_click_threshold:
                            reason = "strong_avatar"
                        else:
                            # Only weaker avatar matches need confirmation.
                            # Either same-card field is enough; an unreadable
                            # artistic name cannot veto a matching race name.
                            race_roi = relative_roi(box, catalog["race_roi_offset"], bounds)
                            name_roi = relative_roi(box, catalog["name_roi_offset"], bounds)
                            if race_roi is not None and verify_card_field(
                                context, image, params["race_node"], race_roi,
                                character["race"], character.get("race_template"), running,
                            ):
                                reason = "avatar_and_race"
                            elif name_roi is not None and verify_card_field(
                                context, image, params["name_node"], name_roi,
                                character["ocr_name"], character.get("name_template"), running,
                            ):
                                reason = "avatar_and_name"
                            else:
                                LOG.warning("Weaker avatar rejected: character=%s score=%.3f; neither text field passed", character["name"], candidate.score)
                                continue
                        if not running():
                            return False
                        # Framework actions transform normalized coordinates.
                        result = context.run_action(params["click_node"], box=box)
                        LOG.info("Card selection character=%s race=%s score=%.3f reason=%s success=%s", character["name"], character["race"], candidate.score, reason, bool(result and result.success))
                        return bool(result and result.success)
                else:
                    LOG.warning("Avatar not matched: character=%s roi=%s candidates=%s", character["name"], bounds,
                                [(round(r.score, 3), tuple(r.box)) for r in detail.all_results] if detail else [])

                if not running():
                    break
                # Do not issue a full 5-second gesture when the deadline is
                # nearer. Leave the screen still for the remaining time.
                remaining = deadline - time.monotonic()
                if remaining < 5.0:
                    LOG.info("Search deadline too near for another 5000ms swipe; remaining=%.2fs", remaining)
                    wait_while_running(remaining, running)
                    break
                LOG.info("Legend search swipe page=%s duration=5000ms", page)
                result = context.run_action(swipe_node, pipeline_override={swipe_node: {"post_delay": 0}})
                if not result or not result.success:
                    LOG.error("Legend list swipe failed")
                    return False
                # Keep the 1-second settle wait cancellable and inside the
                # search deadline; never recognize a frame before it settles.
                if not wait_while_running(1.0, running):
                    break
                page += 1

            LOG.error("No validated card: character=%s, stopped or search timed out after %sms", character["name"], params["timeout_ms"])
            return False
        except Exception:
            LOG.exception("Legend card selection failed")
            return False
