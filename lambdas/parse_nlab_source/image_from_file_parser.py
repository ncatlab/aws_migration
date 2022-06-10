import enum
import json
import os
import requests
import urllib.parse

import nlab_mistletoe
import nlab_parsing_errors

_root_url = os.environ["ROOT_URL"]
_file_root_url = os.environ["FILE_ROOT_URL"]

class SizeUnit(enum.Enum):
    PIXELS = "px"
    EM = "em"

class Float(enum.Enum):
    LEFT = "left"
    RIGHT = "right"

class ImageFromFileException(nlab_parsing_errors.NLabSyntaxError):
    def __init__(self, message):
        super().__init__(message)

class _ImageFileDoesNotExistException(Exception):
    pass

class _InvalidMarginJsonException(Exception):
    def __init__(self, message):
        super().__init__(message)

def _check_exists(file_name):
    response = requests.head(os.path.join(
        _root_url,
        _file_root_url.lstrip("/"),
        file_name))
    if response.status_code != 200:
        raise _ImageFileDoesNotExistException()

def _margin(margin_json):
    if not isinstance(margin_json, dict):
        raise _InvalidMarginJsonException(
            "The value of 'margin' should be a JSON with keys 'top', " +
            "'right', 'bottom', 'left', and optionally 'unit',")
    keys = margin_json.keys()
    if "unit" in keys:
        permitted_keys = [ "bottom", "left", "right", "top", "unit" ]
    else:
        permitted_keys = [ "bottom", "left", "right", "top" ]
    if sorted(margin_json.keys()) != permitted_keys:
       raise _InvalidMarginJsonException(
            "The value of 'margin' should be a JSON with keys 'top', " +
            "'right', 'bottom', 'left', and optionally 'unit',")
    try:
        top = int(margin_json["top"])
    except ValueError:
        raise _InvalidMarginJsonException(
            "The value of 'top' in the 'margin' block should be an integer")
    try:
        right = int(margin_json["right"])
    except ValueError:
        raise _InvalidMarginJsonException(
            "The value of 'right' in the 'margin' block should be an integer")
    try:
        bottom = int(margin_json["bottom"])
    except ValueError:
        raise _InvalidMarginJsonException(
            "The value of 'bottom' in the 'margin' block should be an integer")
    try:
        left = int(margin_json["left"])
    except ValueError:
        raise _InvalidMarginJsonException(
            "The value of 'left' in the 'margin' block should be an integer.")
    try:
        unit = SizeUnit(margin_json["unit"])
    except KeyError:
        unit = SizeUnit.PIXELS
    except ValueError:
        raise ImageFromFileException(
            "The value of 'unit' in the 'margin' block must be one of " +
            "the following: " +
            ", ".join([ unit.value for unit in SizeUnit ]))
    return "{}{} {}{} {}{} {}{}".format(
        top,
        unit.value,
        right,
        unit.value,
        bottom,
        unit.value,
        left,
        unit.value)

def _parse_file_name(image_from_file_block):
    try:
        file_name = image_from_file_block["file_name"]
    except KeyError:
        raise ImageFromFileException(
            "No key 'file_name'")
    try:
        _check_exists(file_name)
    except _ImageFileDoesNotExistException:
        raise ImageFromFileException(
            "No image with name {}".format(file_name))
    return file_name

def _parse_width(image_from_file_block):
    try:
        width = int(image_from_file_block["width"])
    except KeyError:
        width = None
    except ValueError:
        raise ImageFromFileException(
            "The value of 'width' must be an integer")
    return width

def _parse_height(image_from_file_block):
    try:
        height = int(image_from_file_block["height"])
    except KeyError:
        height = None
    except ValueError:
        raise ImageFromFileException(
            "The value of 'height' must be an integer")
    return height

def _parse_unit(image_from_file_block):
    try:
        unit = SizeUnit(image_from_file_block["unit"])
    except KeyError:
        unit = SizeUnit.PIXELS
    except ValueError:
        raise ImageFromFileException(
            "The value of 'unit' must be one of the following: " +
            ", ".join([ unit.value for unit in SizeUnit ]))
    return unit

def _parse_alt(image_from_file_block):
    try:
        alt = image_from_file_block["alt"]
    except KeyError:
        alt = None
    return alt

def _parse_float_type(image_from_file_block):
    try:
        float_type = Float(image_from_file_block["float"])
    except KeyError:
        float_type = None
    except ValueError:
        raise ImageFromFileException(
            "The value of 'float' must be one of the following: " +
            ", ".join([ float_type.value for float_type in Float ]))
    return float_type

def _parse_margin(image_from_file_block):
    try:
        margin = _margin(image_from_file_block["margin"])
    except KeyError:
        margin = None
    except _InvalidMarginJsonException as invalid_margin_json_exception:
        raise ImageFromFileException(str(invalid_margin_json_exception))
    return margin

def _parse_caption(image_from_file_block):
    try:
        caption = image_from_file_block["caption"]
    except KeyError:
        caption = None
    if caption:
        caption = nlab_mistletoe.render(caption)
    return caption

def _parse(image_from_file_block):
    width = _parse_width(image_from_file_block)
    height = _parse_height(image_from_file_block)
    if (width is not None) or (height is not None):
        unit = _parse_unit(image_from_file_block)
    else:
        unit = None
    return {
        "file_name": _parse_file_name(image_from_file_block),
        "width": width,
        "height": height,
        "unit": unit,
        "alt": _parse_alt(image_from_file_block),
        "float_type": _parse_float_type(image_from_file_block),
        "margin": _parse_margin(image_from_file_block),
        "caption": _parse_caption(image_from_file_block)
    }

def _create_img_tag(parameters):
    image_html = "<img src=\"{}\"".format(os.path.join(
        _file_root_url,
        urllib.parse.quote(parameters["file_name"])))
    width = parameters["width"]
    if width:
       image_html = "{} width=\"{}{}\"".format(
           image_html,
           width,
           parameters["unit"].value)
    height = parameters["height"]
    if height:
       image_html = "{} height=\"{}{}\"".format(
           image_html,
           height,
           parameters["unit"].value)
    alt = parameters["alt"]
    if alt:
       image_html = "{} alt=\"{}\"".format(alt)
    return image_html + "/>"

def _create_figure(parameters):
    img_tag = _create_img_tag(parameters)
    caption = parameters["caption"]
    if caption:
        figure = (
            "<figure style=\"margin: 0 0 0 0\">\n" +
            img_tag +
            "\n<figcaption style=\"text-align: center\">" +
            caption +
            "</figcaption>\n" +
            "</figure>")
    else:
        figure = img_tag
    float_type = parameters["float_type"]
    margin = parameters["margin"]
    if float_type:
        if float_type == Float.RIGHT:
            if margin:
                return (
                    "<div style=\"float: right; " +
                    "margin: {}\">\n{}\n</div>".format(
                        margin,
                        figure))
            else:
                return "<div style=\"float: right\">\n{}\n</div>".format(
                    figure)
        elif margin:
            return "<div style=\"margin: {}; float: {}\">\n{}\n</div>".format(
                margin,
                float_type.value,
                figure)
        else:
            return "<div style=\"float: {}\">\n{}\n</div>".format(
                float_type.value,
                figure)
    if margin:
        return "<div style=\"margin: {}\">\n{}\n</div>".format(
            margin,
            figure)

def render(image_from_file_block):
    image_from_file_block = image_from_file_block.strip()
    try:
        image_from_file_block_json = json.loads(
            "{" + image_from_file_block + "}")
    except json.JSONDecodeError as jsonDecodeError:
        raise nlab_parsing_errors.NLabSyntaxError(
            "An \\image from file{...} block must be in JSON format, except " +
            "that curly brackets should not be used at the beginning and " +
            "end. This is not the case for: " +
            image_from_file_block)
    try:
        return _create_figure(_parse(image_from_file_block_json))
    except ImageFromFileException as exception:
        raise nlab_parsing_errors.NLabSyntaxError("{} in\n\n{}".format(
            str(exception),
            image_from_file_block))


