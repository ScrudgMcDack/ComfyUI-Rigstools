"""
@author: scrudgmcdack
@title: Rigstools
@nickname: rigstools
@version: 1.1.0
@project: https://github.com/ScrudgMcDack/ComfyUI-Rigstools
@description: Load images with their generation data (PNG, JPEG, WebP) and read it back: workflow, prompt and A1111-style parameters
              (seed, steps, CFG, size, prompts, model, LoRA stack); save images with the parameters collected from the graph;
              colour correction. Based on ComfyUI-Crystools by Crystian.
"""

from .core import version, logger
logger.info(f'Rigstools version: {version}')

from .nodes._names import CLASSES
from .nodes.metadata import CMetadataExtractor
from .nodes.parameters import CParamExtractor
from .nodes.lora_hashes import CLoraHashes
from .nodes.image import CLoadImageMeta, CLoadImageFolder
from .nodes.image_params import CLoadImageParams
from .nodes.color import CColorCorrection
from .nodes.save import CSaveImage

NODE_CLASS_MAPPINGS = {
    CLASSES.CMETADATA_EXTRACTOR_NAME.value: CMetadataExtractor,
    CLASSES.CPARAM_EXTRACTOR_NAME.value: CParamExtractor,
    CLASSES.CLORA_HASHES_NAME.value: CLoraHashes,
    CLASSES.CLOAD_IMAGE_META_NAME.value: CLoadImageMeta,
    CLASSES.CLOAD_IMAGE_FOLDER_NAME.value: CLoadImageFolder,
    CLASSES.CLOAD_IMAGE_PARAMS_NAME.value: CLoadImageParams,
    CLASSES.CCOLOR_CORRECTION_NAME.value: CColorCorrection,
    CLASSES.CSAVE_IMAGE_NAME.value: CSaveImage,
}

# output tooltips (English here, Russian in locales/ru/nodeDefs.json) — see core/tooltips.py
from .core.tooltips import output_tooltips as _tips
for _name, _cls in NODE_CLASS_MAPPINGS.items():
    _cls.OUTPUT_TOOLTIPS = _tips(_name, _cls.RETURN_NAMES)

NODE_DISPLAY_NAME_MAPPINGS = {
    CLASSES.CMETADATA_EXTRACTOR_NAME.value: CLASSES.CMETADATA_EXTRACTOR_DESC.value,
    CLASSES.CPARAM_EXTRACTOR_NAME.value: CLASSES.CPARAM_EXTRACTOR_DESC.value,
    CLASSES.CLORA_HASHES_NAME.value: CLASSES.CLORA_HASHES_DESC.value,
    CLASSES.CLOAD_IMAGE_META_NAME.value: CLASSES.CLOAD_IMAGE_META_DESC.value,
    CLASSES.CLOAD_IMAGE_FOLDER_NAME.value: CLASSES.CLOAD_IMAGE_FOLDER_DESC.value,
    CLASSES.CLOAD_IMAGE_PARAMS_NAME.value: CLASSES.CLOAD_IMAGE_PARAMS_DESC.value,
    CLASSES.CCOLOR_CORRECTION_NAME.value: CLASSES.CCOLOR_CORRECTION_DESC.value,
    CLASSES.CSAVE_IMAGE_NAME.value: CLASSES.CSAVE_IMAGE_DESC.value,
}

WEB_DIRECTORY = "./web"  # alembic icon in the node titles, metadata badge of the loaders
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
