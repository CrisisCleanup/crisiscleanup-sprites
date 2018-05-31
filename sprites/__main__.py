import argparse
import sys
import traceback
import json
from os.path import join as path_join
from os.path import basename

from PIL import Image

from sprites.utils import list_files_with_extensions
from sprites.spritify import SpriteGenerator

def load_indicators_from_directory(base_directory):
    png_paths = list_files_with_extensions(base_directory, [".png"])
    result = {}
    for png_path in png_paths:
        image = Image.open(png_path)
        indicator_name = basename(png_path).replace(".png","")
        result[indicator_name] = image
    
    return result

def parse_args():
    parser = argparse.ArgumentParser(description="A script to transform "
                                     "source icons into sprites using a "
                                     "set of transformation rules for "
                                     "representing status/age/claim state")
    parser.add_argument("-r","--resources", 
                        help="The root resources directory containing directories"
                        " for source icons, configuration, and other resources.",
                        required=True)
    
    parser.add_argument("-a","--artifacts", 
                        help="The root directory to use for outputs.",
                        default="./artifacts")
    
    return vars(parser.parse_args())

def main():
    #indicators created using: http://www.xiconeditor.com/
    parsed_args = parse_args()
    resource_dir = parsed_args["resources"]
    artifacts_dir = parsed_args["artifacts"]
    image_definition_json_path = path_join(resource_dir,"config", "image_definitions.json")
    closed_base_path = path_join(resource_dir, "source_icons", "x.png")
    
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
        
    indicator_dir = path_join(resource_dir, "icon_indicators")
    overlay_dir = path_join(resource_dir, "overlays")
    
    generator = SpriteGenerator(image_definition_json, 
                                closed_base, 
                                excluded_paths=[closed_base_path],
                                indicators = load_indicators_from_directory(indicator_dir),
                                overlays = load_indicators_from_directory(overlay_dir))
    
    source_dir = path_join(resource_dir, "source_icons")
    generator.generate_from_directory(source_dir, artifacts_dir)

if __name__=="__main__":
    main()
