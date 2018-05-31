import argparse
import json
import math
import sys
import traceback
from os import listdir, makedirs
from os.path import isfile, splitext, basename
from os.path import join as path_join

from PIL import Image, ImageFilter

#how many pixels should be allocated for each icon
#in a sprite
SPRITE_ICON_SPACING = 50

#Formula for the position of an icon within a sprite:
#   icon_left = <column_index>*SPRITE_ICON_SPACING
#   icon_right = (1 + <column_index>)*SPRITE_ICON_SPACING
#   icon_top = <row_index>*SPRITE_ICON_SPACING
#   icon_bottom = (1 + <row_index>)*SPRITE_ICON_SPACING
#Note that the right and bottom coordinates given are maximums;
#for a given icon their values may be slightly less.

SPRITE_COLUMNS = [
    {"claim-status" : "unclaimed", "age" : "new"},
    {"claim-status" : "unclaimed", "age" : "old1"},
    {"claim-status" : "unclaimed", "age" : "old2"},
    {"claim-status" : "unclaimed", "age" : "old3"},
    {"claim-status" : "unclaimed", "age" : "old4"},
    {"claim-status" : "unclaimed", "age" : "old5"},
    {"claim-status" : "claimed", "age" : "new"},
    {"claim-status" : "claimed", "age" : "old1"},
    {"claim-status" : "claimed", "age" : "old2"},
    {"claim-status" : "claimed", "age" : "old3"},
    {"claim-status" : "claimed", "age" : "old4"},
    {"claim-status" : "claimed", "age" : "old5"}
    ]

SPRITE_ROWS = [
    {"is-multi" : False, "status_string" : "open_unassigned"},
    {"is-multi" : False, "status_string" : "open_assigned"},
    {"is-multi" : False, "status_string" : "open_partially_completed"},
    {"is-multi" : False, "status_string" : "open_partially_needs_follow_up"},
    {"is-multi" : False, "status_string" : "open_unresponsive"},
    {"is-multi" : False, "status_string" : "closed_completed"},
    {"is-multi" : False, "status_string" : "closed_incomplete"},
    {"is-multi" : False, "status_string" : "closed_out_of_scope"},
    {"is-multi" : False, "status_string" : "closed_done_by_others"},
    {"is-multi" : False, "status_string" : "closed_no_help_wanted"},
    {"is-multi" : False, "status_string" : "closed_rejected"},
    {"is-multi" : False, "status_string" : "closed_duplicate"},
    {"is-multi" : False, "status_string" : "closed_marked_for_deletion"},
    {"is-multi" : True, "status_string" : "open_unassigned"},
    {"is-multi" : True, "status_string" : "open_assigned"},
    {"is-multi" : True, "status_string" : "open_partially_completed"},
    {"is-multi" : True, "status_string" : "open_partially_needs_follow_up"},
    {"is-multi" : True, "status_string" : "open_unresponsive"},
    {"is-multi" : True, "status_string" : "closed_completed"},
    {"is-multi" : True, "status_string" : "closed_incomplete"},
    {"is-multi" : True, "status_string" : "closed_out_of_scope"},
    {"is-multi" : True, "status_string" : "closed_done_by_others"},
    {"is-multi" : True, "status_string" : "closed_no_help_wanted"},
    {"is-multi" : True, "status_string" : "closed_rejected"},
    {"is-multi" : True, "status_string" : "closed_duplicate"},
    {"is-multi" : True, "status_string" : "closed_marked_for_deletion"}
    ]

def get_icon_class(*dicts):
    class_dict = {}
    for d in dicts:
        class_dict.update(d)
    
    icon_class = (class_dict["status_string"] + "-"
                  + class_dict["claim-status"] + "-"
                  + class_dict["age"] + "-"
                  + ("multi" if class_dict["is-multi"] else "single"))
    
    return icon_class

class SpriteGenerator(object):
    """
    Object for transforming icons into sprites
    """
    SUPPORTED_ICON_FORMATS = [".png"]
    
    """
    Pixels in icons are pretty much in one of two
    states (ignoring overlays), on and of the same
    color as all other "on" pixels, or transparent.
    We try to bin pixels into one of these two 
    categories by looking at the value of the alpha
    channel, and this is the magnitude at which a pixel
    is considered "on"
    """
    ALPHA_CHANNEL_THRESHOLD = 75
    
    def __init__(self, image_definition_json, closed_base_image, **kwargs):
        self._image_definition_json = image_definition_json
        self._closed_base_image = closed_base_image
        self._excluded_paths = set(kwargs.get("excluded_paths", []))
        self._indicators = kwargs["indicators"]
        self._overlays = kwargs["overlays"]
    
    def _convert_to_hsv_alpha(self, indicator):
        r, g, b, a = indicator.convert("RGBA").split()
        indicator = Image.merge("RGB", (r, g, b)).convert("HSV")
        
        return indicator, a
    
    def _get_icons_to_transform(self, source_directory):
        """
        Returns the paths for the icons to generate sprites from
        """
        all_paths =  _list_files_with_extensions(source_directory,
                                           SpriteGenerator.SUPPORTED_ICON_FORMATS)
        return [p for p in all_paths if p not in self._excluded_paths]
    
    def generate_from_directory(self, source_directory):
        """
        Apply the transformation on all icons
        """
        source_icon_paths = self._get_icons_to_transform(source_directory)
        for source_icon_path in source_icon_paths:
            sprite_icons = self.generate_from_icon(Image.open(source_icon_path), 
                                                   apply_colorblind_transforms = False)
            self._write_sprite_directory(sprite_icons, source_icon_path)
            self._write_sprite(sprite_icons, source_icon_path)
            
            colorblind_sprite_icons = self.generate_from_icon(Image.open(source_icon_path),
                                                   apply_colorblind_transforms = True)
            self._write_sprite(colorblind_sprite_icons, source_icon_path, suffix="-colorblind")
            
    def _write_sprite(self, sprite_icons, source_icon_path, suffix=""):
        """
        Create a single image file containing icons "quilted" to form sprite
        
        Arguments:
            sprite_icons: A dict from icon class to image object
            source_icon_path: the full path to the source icon generating 
                the sprite icons.
            suffix: Will be appended to the image name of the sprite.
        """
        rows_as_images = []
        for row_dict in SPRITE_ROWS:
            images_in_row = []
            for column_dict in SPRITE_COLUMNS:
                icon_class = get_icon_class(row_dict, column_dict)
                icon = sprite_icons[icon_class]
                images_in_row.append(icon)
            row_image = append_images(images_in_row,
                                      "horizontal", 
                                      "top", 
                                      image_extent=SPRITE_ICON_SPACING)
            rows_as_images.append(row_image)
        
        sprite = append_images(rows_as_images,
                      "vertical",
                      "left",
                      image_extent=SPRITE_ICON_SPACING)
        
        sprite_directory = splitext(source_icon_path)[0]
        makedirs(sprite_directory, exist_ok=True)
        
        source_name = basename(sprite_directory)
        file_name = path_join(sprite_directory, source_name+"-sprite"+suffix+".png")
        sprite.save(file_name)
            
    
    def _write_sprite_directory(self, sprite_icons, source_icon_path):
        """
        Create a directory containing all permutations of a source icon
        
        Arguments:
            sprite_icons: A dict from icon class to image object
            source_icon_path: the full path to the source icon generating 
                the sprite icons.
        """
        sprite_directory = splitext(source_icon_path)[0]
        makedirs(sprite_directory, exist_ok=True)
        
        source_name = basename(sprite_directory)
        for icon_class, sprite_icon in sprite_icons.items():
            file_name = path_join(sprite_directory, source_name+"-"+icon_class+".png")
            try:
                sprite_icon.save(file_name)
            except IOError:
                traceback.print_exc()
                print("cannot convert icon '{}' with icon class '{}'".format(source_name,icon_class))

    
    def generate_from_icon(self, icon, apply_colorblind_transforms = False):
        """
        Create a sprite for an icon located at the specified path
        """
        icon = icon.convert("RGBA")
        alpha_channel = icon.split()[3]
        
        hsv_icon = icon.convert("HSV")
        transform_configs = self._get_transform_configs()
        sprite_icons = {}
        for sprite_icon_class, transform_config in transform_configs.items():
            sprite_icon = self._apply_transforms(hsv_icon, 
                                                 alpha_channel, 
                                                 transform_config,
                                                 apply_colorblind_transforms)
            sprite_icons[sprite_icon_class] = sprite_icon
        
        return sprite_icons
    
    def _get_transform_configs(self):
        """
        Get a dictionary mapping from sprite icon class to transforms
        
        Sprite icon class is a string that identifies the status, 
        claim state, and age of an icon completely. Each transform
        specifies how the corresponding source icon should be changed
        to produce the sprite icon for that sprite icon class.
        """
        return self._image_definition_json
    
    def _apply_transforms(self, hsv_icon, alpha_channel, transform_config, apply_colorblind_transforms = False):
        """
        For a given set of icon transforms, apply them and produce result
        
        For instance, for a specific status/claim state/age the hue might
        need to be rotated by x, the transparency changed by y, etc.
        """
        transforms = [
                ("use-closed-base", self._use_closed_base),
                ("color", self._set_color),
                ("hue-rotate", self._rotate_hue),
                ("grayscale", self._make_grayscale),
                ("opacity", self._set_opacity)
            ]
        for transform_key, transform_func in transforms:
            if transform_func is None:
                continue
            if transform_key not in transform_config:
                continue
            transform_value = transform_config[transform_key]
            hsv_icon, alpha_channel = transform_func(hsv_icon, alpha_channel, transform_value)
        
        r, g, b = hsv_icon.convert("RGB").split()
        sprite_icon = Image.merge("RGBA", (r, g, b, alpha_channel))
        sprite_icon = self._add_dropshadow(sprite_icon)
        
        if apply_colorblind_transforms:
            sprite_icon = self._add_colorblind_indicators(sprite_icon, 
                                           transform_config.get("colorblind-indicators",[]))
        else:
            sprite_icon = self._add_overlays(sprite_icon,
                                             transform_config.get("overlays",[]))
            
        return sprite_icon
        
    @staticmethod
    def _add_dropshadow(sprite_icon):
        shadow = SpriteGenerator._create_shadow(sprite_icon)
        
        sprite_icon = Image.alpha_composite(shadow, sprite_icon)
        
        return sprite_icon
    
    @staticmethod
    def _create_shadow(sprite_icon):
        """
        Create a shadow (without the image it's shadowing)
        """
        shadow_lightness = 0 #what shade should the shadow be?
        
        #what is the opacity at which something deserves shadowing?
        shadow_channel_threshold = SpriteGenerator.ALPHA_CHANNEL_THRESHOLD
        blur_radius = 2 #how "blurry" should the shadow be?
        
        shadow_offset = 1
        
        alpha_channel = sprite_icon.split()[3]
        
        #shadow channel is low where the image is, 255 elsewhere
        shadow_channel_filter = lambda i: shadow_lightness if i>shadow_channel_threshold else 255
        shadow_channel = alpha_channel.point(shadow_channel_filter)
        
        #A version of the icon that is completely black
        grayscale_icon = Image.merge("RGBA", (shadow_channel, shadow_channel, shadow_channel, alpha_channel))
        width, height = grayscale_icon.size
        
        offset_icon = Image.new('RGBA', (width + shadow_offset, height + shadow_offset), color=(255,255,255,0))
        offset_icon.paste(grayscale_icon, (shadow_offset, shadow_offset))
                
        shadow = offset_icon.filter(ImageFilter.GaussianBlur(blur_radius))
        
        #crop to original size
        crop_box = (0, 0, width, height)
        shadow = shadow.crop(crop_box)
        
        return shadow
        
        
    @staticmethod
    def _rotate_hue(hsv_icon, alpha_channel, rotation_amount):
        HUE, SATURATION, VALUE = 0,1,2
        hsv_channels = hsv_icon.split()
        adapted_hue_channel = hsv_channels[HUE].point(lambda h: (h+rotation_amount+360) % 360)
        
        hsv_channels = adapted_hue_channel, hsv_channels[SATURATION], hsv_channels[VALUE]
        
        return Image.merge("HSV", hsv_channels), alpha_channel
    
    @staticmethod
    def _set_color(hsv_icon, alpha_channel, hsv_json):
        """
        Set the color of "on" pixels using hue/saturation/value
        """
        HUE, SATURATION, VALUE = 0,1,2
        hsv_channels = hsv_icon.split()
        
        #Determine which pixels are "on" and which are "off"
        #using the alpha channel        
        alpha_mask = [a>SpriteGenerator.ALPHA_CHANNEL_THRESHOLD for a in alpha_channel.getdata()]

        hue_data = [hsv_json["hue"] if is_on else 0 for is_on in alpha_mask]
        if "saturation-multiplier" in hsv_json:
            saturation_transform = lambda s: int(max(0, min(255, hsv_json["saturation-multiplier"]*s)))
        else:
            saturation_transform = lambda s: s
        if "value-multiplier" in hsv_json:
            value_transform = lambda v: int(max(0, min(255, hsv_json["value-multiplier"]*v)))
        else:
            value_transform = lambda v: v
        
        hsv_channels[HUE].putdata(hue_data)
        saturation_channel = hsv_channels[SATURATION].point(saturation_transform)
        value_channel = hsv_channels[VALUE].point(value_transform)
        
        hsv_channels = (hsv_channels[HUE], saturation_channel, value_channel)
        result = Image.merge("HSV", hsv_channels)
        
        return result, alpha_channel
    
    @staticmethod
    def _set_opacity(hsv_icon, alpha_channel, opacity):
        alpha_channel = alpha_channel.point(
            lambda a: int(math.floor(a*opacity)))
        return hsv_icon, alpha_channel
    
    @staticmethod
    def _make_grayscale(hsv_icon, alpha_channel, is_greyscale):
        if not is_greyscale:
            return hsv_icon, alpha_channel
        
        #You can convert between RGB and L/HSV, but not HSV and L
        return hsv_icon.convert("L").convert("RGB").convert("HSV"), alpha_channel
    
    def _add_colorblind_indicators(self, icon, indicator_list):
        """
        Add a bar of tiny indicators to the right of the icons
        this will be used for an alternate sprite (one designed
        specifically for the colorblind)
        Arguments:
            icon: the icon, in RGBA format
            indicator_list: A list of strings, each string 
                identifying an indicator
        """
        if not indicator_list:
            return icon
        
        indicator_bar = self.generate_indicator_bar(indicator_list)
        icon = append_images([icon, indicator_bar], 
                          "horizontal", 
                          "top")
        
        return icon
    
    def _add_overlays(self, icon, overlay_list):
        for overlay_string in overlay_list:
            overlay = self._overlays[overlay_string]
            overlay = self._pad_image(overlay, icon.size)
            icon = Image.alpha_composite(icon, overlay)
        return icon
    
    @staticmethod
    def _pad_image(image, to_size):
        width, height = to_size
        current_width, current_height = image.size
        new_image = Image.new('RGBA', (max(width, current_width), max(height, current_height)), color=(255,255,255,0))
        new_image.paste(image, (0, 0))
        
        return new_image.crop((0, 0, width, height))
    
    def generate_indicator_bar(self, indicator_list):
        icons = []
        for indicator_name in indicator_list:
            icon = self._indicators[indicator_name]
            icons.append(icon)
            
        icon = append_images(icons,
                             "vertical",
                             "left",
                             padding_pixels=2)
        
        return icon
    
    def _use_closed_base(self, hsv_icon, alpha_channel, use_closed_base):
        if not use_closed_base:
            return hsv_icon, alpha_channel
        
        icon = self._closed_base_image.convert("RGBA")
        alpha_channel = icon.split()[3]
        
        hsv_icon = icon.convert("HSV")
        
        return hsv_icon, alpha_channel
        
    
def _list_files_with_extensions(directory, extensions=None):
    extensions = extensions if extensions is not None else [""]
    include = lambda d, f: (isfile(path_join(d, f)) 
                            and any(f.endswith(extension) for extension in extensions))
    
    return [path_join(directory, f) for f in listdir(directory) if include(directory, f)]

def parse_args():
    parser = argparse.ArgumentParser(description="A script to transform "
                                     "source icons into sprites using a "
                                     "set of transformation rules for "
                                     "representing status/age/claim state")
    parser.add_argument("-d","--directory", 
                        help="The directory containing the source icons",
                        required=True)
    
    return vars(parser.parse_args())


def append_images(images, direction='horizontal', aligment='center', padding_pixels=0, image_extent=None):
    """
    Appends images in horizontal/vertical direction.

    Args:
        images: List of PIL images,
        direction: direction of concatenation, 'horizontal' or 'vertical'
        aligment: alignment mode if images need padding;
           'left', 'right', 'top', 'bottom', or 'center',
        padding_pixels: how many pixels to insert between images.
            Cannot be used with image_extent
        image_extent:
            The width that horizontal images will be alloted,
            or the height that vertical images will be alloted.
            Cannot be used with padding_pixels
        

    Returns:
        Concatenated image as a new PIL image object.
    """
    #Note: based on https://stackoverflow.com/a/46623632/2540669
    
    widths, heights = zip(*(i.size for i in images))

    if direction=='horizontal':
        if image_extent is None:
            new_width = sum(widths)+padding_pixels*(len(images)-1)
        else:
            new_width = len(images)*image_extent
        new_height = max(heights)
    else:
        new_width = max(widths)
        if image_extent is None:
            new_height = sum(heights)+padding_pixels*(len(images)-1)
        else:
            new_height = len(images)*image_extent

    new_im = Image.new('RGBA', (new_width, new_height), color=(255,255,255,0))

    offset = 0
    for im in images:
        if direction=='horizontal':
            y = 0
            if aligment == 'center':
                y = int((new_height - im.size[1])/2)
            elif aligment == 'bottom':
                y = new_height - im.size[1]
            new_im.paste(im, (offset, y))
            offset += im.size[0]+padding_pixels if image_extent is None else image_extent
        else:
            x = 0
            if aligment == 'center':
                x = int((new_width - im.size[0])/2)
            elif aligment == 'right':
                x = new_width - im.size[0]
            new_im.paste(im, (x, offset))
            offset += im.size[1]+padding_pixels if image_extent is None else image_extent

    return new_im

def load_indicators_from_directory(base_directory):
    png_paths = _list_files_with_extensions(base_directory, [".png"])
    result = {}
    for png_path in png_paths:
        image = Image.open(png_path)
        indicator_name = basename(png_path).replace(".png","")
        result[indicator_name] = image
    
    return result

def main():
    #indicators created using: http://www.xiconeditor.com/
    parsed_args = parse_args()
    source_dir = parsed_args["directory"]
    image_definition_json_path = path_join(source_dir, "image_definitions.json")
    closed_base_path = path_join(source_dir, "x.png")
    
    try:
        with open(image_definition_json_path, "r") as f:
            image_definition_json = json.load(f)
    except Exception:
        traceback.print_exc()
        image_definition_json = None
        print("Could not read image definition json")
        sys.exit()
        
    try:
        closed_base = Image.open(closed_base_path)
    except Exception:
        traceback.print_exc()
        closed_base = None
        print("Could not read closed base image")
        sys.exit()
        
    indicator_dir = path_join(source_dir, "_icon_indicators")
    overlay_dir = path_join(source_dir, "_overlays")
    
    generator = SpriteGenerator(image_definition_json, 
                                closed_base, 
                                excluded_paths=[closed_base_path],
                                indicators = load_indicators_from_directory(indicator_dir),
                                overlays = load_indicators_from_directory(overlay_dir))
    
    generator.generate_from_directory(source_dir)

if __name__=="__main__":
    main()
