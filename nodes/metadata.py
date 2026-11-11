import json
from ..core import CATEGORY, CONFIG, METADATA_RAW, TEXTS, logger
from ..core.prompt_graph import parameters_from_prompt as rebuild_parameters
from ..core.settings import debug
from .image import metadata_lines

KNOWN_KEYS = ("prompt", "workflow", "fileinfo", "parameters")


class CMetadataExtractor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "metadata_raw": (METADATA_RAW[0], {**METADATA_RAW[1], "tooltip": "File metadata: the METADATA_RAW "
                                                                             "output of a Rigstools or Crystools loader"}),
            },
            "optional": {
                "parameters_from_prompt": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "When the image has no A1111-style parameters (e.g. saved by the stock Save Image), "
                               "rebuild them from the ComfyUI prompt stored in the image",
                }),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    CATEGORY = CATEGORY.MAIN.value + CATEGORY.METADATA.value

    RETURN_TYPES = ("JSON", "JSON", "JSON", "STRING", "JSON", "STRING", "STRING")
    RETURN_NAMES = ("PROMPT", "WORKFLOW", "FILEINFO", "PARAMETERS", "RAW2JSON", "RAW2PROPERTIES", "RAW2CSV")

    DESCRIPTION = (
        "Splits the metadata of an image into separate outputs: the ComfyUI prompt and workflow, file info and the "
        "A1111-style \"parameters\" text with the main generation parameters. Full metadata — as JSON, key=value "
        "lines and CSV.\n"
        "For images without \"parameters\" (e.g. from the stock Save Image): the parameters are rebuilt from the "
        "ComfyUI prompt.\n"
        "Input: METADATA_RAW from \"Load image with metadata\" (Rigstools or Crystools)."
    )

    FUNCTION = "execute"

    def execute(self, metadata_raw=None, parameters_from_prompt=True, unique_id=None):
        indent = CONFIG["indent"]
        prompt, workflow, fileinfo, parameters = {}, {}, {}, ""
        rebuilt = False
        props, csv = "", ""

        if isinstance(metadata_raw, dict):
            try:
                for key, value in metadata_raw.items():
                    # nested objects are serialised to JSON first, so every value becomes one quoted string
                    as_text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
                    quoted = json.dumps(as_text, ensure_ascii=False)
                    props += f'"{key}"={quoted}\n'
                    csv += f'"{key}"\t{quoted}\n'
                if csv:
                    csv = '"key"\t"value"\n' + csv
            except Exception as e:
                logger.warning(e)

            prompt = metadata_raw.get("prompt") or {}
            workflow = metadata_raw.get("workflow") or {}
            fileinfo = metadata_raw.get("fileinfo") or {}
            parameters = metadata_raw.get("parameters") or ""

            if not parameters and parameters_from_prompt and prompt:
                try:
                    parameters = rebuild_parameters(prompt)
                    rebuilt = bool(parameters)
                except Exception as e:
                    logger.warning(f"Could not rebuild parameters from the prompt: {e}")
                    parameters = ""

            info = {"parameters": bool(metadata_raw.get("parameters")), "prompt": bool(prompt),
                    "workflow": bool(workflow), "rebuilt": rebuilt}
            name = fileinfo.get("filename") if isinstance(fileinfo, dict) else None
            name = name.replace("\\", "/").rsplit("/", 1)[-1] if isinstance(name, str) else None
            debug("\n".join([f"Metadata extractor #{unique_id}: reading the metadata" + (f" of {name}" if name else "")]
                             + metadata_lines(info, rebuild=parameters_from_prompt)
                             + ([] if parameters or not prompt else ["  the PARAMETERS output is empty"])))

        elif metadata_raw is None:
            debug(f"Metadata extractor #{unique_id}: no metadata_raw connected, all outputs are empty")
        else:
            logger.warning(TEXTS.INVALID_METADATA_MSG.value)

        # state of the outputs for the node (dimmed / ✕ / ↻ in web/rigstools.js)
        state = {"off": [k for k, v in (("PROMPT", prompt), ("WORKFLOW", workflow), ("FILEINFO", fileinfo)) if not v],
                 "rebuilt": ["PARAMETERS"] if rebuilt else [], "reasons": {}}
        for k in state["off"]:
            state["reasons"][k] = {"code": "noBlock", "v": k.lower()}
        if not parameters:
            state["off"].append("PARAMETERS")
            state["reasons"]["PARAMETERS"] = {"code": "noParamsRebuild" if (prompt and parameters_from_prompt)
                                              else "noParamsOff" if prompt else "noParams"}
        if metadata_raw is None:
            state["off"] += ["RAW2JSON", "RAW2PROPERTIES", "RAW2CSV"]
        # what comes out, for the styled tooltips (Draftsman)
        state["values"] = {}
        if isinstance(prompt, dict) and prompt:
            state["values"]["PROMPT"] = {"code": "nodes", "v": len(prompt)}
        if isinstance(workflow, dict) and workflow:
            state["values"]["WORKFLOW"] = {"code": "nodes", "v": len(workflow.get("nodes") or [])}
        if isinstance(fileinfo, dict) and fileinfo:
            state["values"]["FILEINFO"] = {"code": "value", "v": " · ".join(
                str(fileinfo[k]) for k in ("resolution", "size") if fileinfo.get(k))}
        if parameters:
            state["values"]["PARAMETERS"] = {"code": "text", "v": " ".join(parameters.split())[:90]}
        return {"ui": {"rig_state": [state]},
                "result": (json.dumps(prompt, indent=indent, ensure_ascii=False),
                           json.dumps(workflow, indent=indent, ensure_ascii=False),
                           json.dumps(fileinfo, indent=indent, ensure_ascii=False),
                           parameters,
                           json.dumps(metadata_raw, indent=indent, ensure_ascii=False),
                           props, csv)}

