import PIL
import PIL.Image
import PIL.ImageFont
import PIL.ImageOps
import PIL.ImageDraw
from Oracle import Oracle

# I'm considering this as a better way of dealing with long messages
# perhaps in conjunction with the threaded tweets.

PIXEL_ON = 0
PIXEL_OFF = 255

def text_image_from_file(text_path, font_path=None):
    with open(text_path) as text_file:
        lines = tuple(l.rstrip() for l in text_file.readlines())


    total_length = sum([len(l) for l in lines])
    char_width = 60
    sequence = []
    print(lines)
    for line in lines:
        sequence.extend(Oracle.split_by_width(line, char_width, False))
        sequence.append(" ")

    lines = tuple(sequence)
    print(lines)
    grayscale = 'L'

    large_font = 20
    font_path = font_path or 'cour.ttf'
    try:
        font = PIL.ImageFont.truetype(font_path, size=large_font)
    except IOError:
        font = PIL.ImageFont.load_default()
        print('Count not use chosen font. Using default.')

    # make the background image based on the combination of font and lines
    pt2px = lambda pt: int(round(pt * 96.0 / 72))
    max_width_line = max(lines, key=lambda s: font.getsize(s)[0])
    # max height is adjusted down because it's too large visually for spacing
    test_string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    max_height =  pt2px(font.getsize(test_string)[1])
    max_width = pt2px(font.getsize(max_width_line)[0])
    height = max_height * len(lines)    # perfect or a little oversized
    width = int(round(max_width + 40))  # a little oversized
    image = PIL.Image.new(grayscale, (width, height), color=PIXEL_OFF)
    draw = PIL.ImageDraw.Draw(image)

    # draw each line of text
    vertical_position = 5
    horizontal_position = 5
    line_spacing = int(round(max_height * 0.8))  # reduced spacing
    for line in lines:
        draw.text((horizontal_position, vertical_position),
                  line, fill=PIXEL_ON, font=font)
        vertical_position += line_spacing

    # crop the text
    c_box = PIL.ImageOps.invert(image).getbbox()
    image = image.crop(c_box)
    return image

def text_image_usage():
    img = text_image_from_file('render_test.txt')
    img.show()
    img.save('render_test.png')

text_image_usage()