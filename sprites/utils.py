from os.path import join as path_join
from os.path import isfile
from os import listdir
from PIL import Image

def list_files_with_extensions(directory, extensions=None):
    extensions = extensions if extensions is not None else [""]
    include = lambda d, f: (isfile(path_join(d, f)) 
                            and any(f.endswith(extension) for extension in extensions))
    
    return [path_join(directory, f) for f in listdir(directory) if include(directory, f)]

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