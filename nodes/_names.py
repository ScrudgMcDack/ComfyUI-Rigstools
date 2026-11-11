from enum import Enum


# IMPORTANT: don't change the *_NAME values — saved workflows refer to the nodes by them.
# NAME is the node id (search), DESC is the title shown on the canvas; the alembic icon is drawn by web/rigstools.js
class CLASSES(Enum):
    CMETADATA_EXTRACTOR_NAME = 'Metadata extractor [Rigstools]'
    CMETADATA_EXTRACTOR_DESC = 'Metadata extractor'

    CPARAM_EXTRACTOR_NAME = 'Parameters extractor [Rigstools]'
    CPARAM_EXTRACTOR_DESC = 'Parameters extractor'

    CLORA_HASHES_NAME = 'LoRA hashes for Image Saver [Rigstools]'
    CLORA_HASHES_DESC = 'LoRA hashes for Image Saver'

    CLOAD_IMAGE_META_NAME = 'Load image with metadata [Rigstools]'
    CLOAD_IMAGE_META_DESC = 'Load image with metadata'

    CLOAD_IMAGE_FOLDER_NAME = 'Load image from folder [Rigstools]'
    CLOAD_IMAGE_FOLDER_DESC = 'Load image from folder'

    CLOAD_IMAGE_PARAMS_NAME = 'Load image with parameters [Rigstools]'
    CLOAD_IMAGE_PARAMS_DESC = 'Load image with parameters'

    CCOLOR_CORRECTION_NAME = 'Color correction [Rigstools]'
    CCOLOR_CORRECTION_DESC = 'Color correction'

    CSAVE_IMAGE_NAME = 'Save image [Rigstools]'
    CSAVE_IMAGE_DESC = 'Save image'
