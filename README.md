# Crisis Cleanup Sprites

## General

This repository contains code and resources for creating work-order
sprites for the Crisis Cleanup map.

Core to Crisis Cleanup is the map of work orders. This map provides
at-a-glance information about work orders at a given location by
using a combination of icon shape, color, transparency, and overlays
for the pins that mark work-order locations.

One of the primary pieces of information conveyed by the pins is
the work order type (for example, debris removal, mold remediation,
etc.). Each work order type is represented by a particular source icon
(for example, the debris removal source icon is shaped like a trash
can). Other information is communicated by modifying the color or
transparency of the icon or by adding one or more overlays to it.

In order to support mapping libraries that require a simple image
(with no CSS styling) for the map pins, the variations on the source
icons must be computed in advance. This is the primary motivation for
the tooling provided in this repo. Map performance may also be
enhanced by leveraging pre-computed pins rather than pins that are
styled client-side.

Rather than having a unique image file for every possible variation
on each source icon (which might result in a large number of
round-trips for initial map load), the variants are "stitched"
together for each source icon, resulting in a quilt-like sprite for
each source icon. To display one icon from the sprite, simply display
the sprite image with an appropriate offset and width/height.

### Colorblindness

Since information communicated using color can be difficult to
see for colorblind individuals, there are alternate versions
of each sprite produced which have tiny "indicators" displayed
beside the pin icon.

## Installation & Running

To install, run `pip install -e .` from the root of this repository.

After that, generate the sprites by using `python -m sprites -r <resources directory> -a <output directory>`.

The resources directory should be the resources directory in this
repo, or one structured in the same way. The sprites and any other
outputs will be organized and written to the output directory.

## Adding a new work order type

To add the sprites for a new work order type, simply add the source
icon for the new work order type to the
`<resources dir>/source_icons` directory. Once the script has been
run, the sprite & colorblind sprite for it will be available.

- The hue of the new source icon is irrelevant, and will be reset
for each output variant of the icon in the final sprite
- The gradient of the icon *is* important, and will be used in
 all output variants.
- The icon should be a `.png`, and be less than-or-equal to 32
  pixels tall and 27 pixels wide (the extra margin in width is
  used to add the colorblind indicators)

## Changing the appearance of the produced icons

Most of the information regarding the appearance of the produced
variants on the source icons is declared in
`<resource dir>/config/image_definitions.json`

This file is structured as a descriptive string for a combination
of information the resulting icon variant is meant to express,
mapping to configuration for how to display that icon variant.

For example:

```
"open_assigned-claimed-new-single": {
    "color": {
        "hue": 45,
        "value-multiplier": 1.5,
        "saturation-multiplier": 1.5
    },
    "use-closed-base": false,
    "opacity": 1.0,
    "colorblind-indicators": [
        "claimed"
    ],
    "overlays": []
},
```

As a summary of some of the fields:

- **`opacity`**: A float between 0 and 1 for how opaque the icon
  should be
- **`use-closed-base`**: Instead of the source icon, use an "x"
  (`x.png`)
- **colorblind-indicators**: A list of tiny indicators to add to
  the colorblind versions of the icon variants. List elements
  should correspond to the filenames of images in
  `<resource dir>/icon_indicators`
- **overlays**: A list of overlays that should be placed over
  the icon (ex: a plus sign for "multi")
- **color**: The color of the icon variant. Note that this color
  is expressed similarly to an HSV color in that hue, saturation,
  and value are treated separately. However, only the hue is given
  in absolute terms. The saturations and values are given as
  "multipliers". These multipliers refer to how the saturation and
  value of each pixel in the source icon will be manipulated to
  produce the saturation and value that will be used for each pixel
  in the output image. This mechanism is designed to allow for the
  preservation of saturation/value gradients in the source icons.
  Note that to produce a grayscale output icon, the saturation
  multiplier can simply be set to 0.

To change the color of all icon variants representing
`open_assigned-claimed` work orders, for instance, you would
simply find all entries in `image_definitions.json` with this
status and claim state, then change their color field as desired.
