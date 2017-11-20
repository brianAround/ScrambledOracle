import PIL
import PIL.Image
import PIL.ImageFont
import PIL.ImageOps
import PIL.ImageDraw

# I'm considering this as a better way of dealing with long messages
# perhaps in conjunction with the threaded tweets.

PIXEL_ON = 0
PIXEL_OFF = 255

def text_image_from_file(text_path, font_path=None):
    with open(text_path) as text_file:
        lines = tuple(l.rstrip() for l in text_file.readlines())

    sequence = arrange_text(lines)

    lines = tuple(sequence)
    # print(lines)
    return render_text(font_path, lines)

def image_file_path_from_text(source_text, font_path=None, image_path='render_text.png'):
    lines = tuple(l.rstrip() for l in source_text.split('\n'))
    sequence = arrange_text(lines)
    lines = tuple(sequence)
    img = render_text(font_path, lines)
    img.save(image_path)
    return image_path

def render_text(font_path, lines):
    grayscale = 'L'
    large_font = 12
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
    max_height = pt2px(font.getsize(test_string)[1])
    max_width = pt2px(font.getsize(max_width_line)[0])
    height = max_height * len(lines)  # perfect or a little oversized
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


def arrange_text(lines):
    total_length = sum([len(l) for l in lines])
    char_width = int(total_length * 0.1111 + 20)
    if char_width < 30:
        char_width = 30
    elif char_width > 60:
        char_width = 60
    sequence = []
    # print(lines)
    for line in lines:
        sequence.extend(split_by_width(line, char_width, False))
        sequence.append(" ")
    return sequence


def split_by_width(src_text, allow_length, try_balance=True):
    parts = []
    partsizes = []
    words = src_text.split()
    if try_balance:
        midword = int(len(words) / 2)
        parts.append(words[:midword])
        partsizes.append(sum([len(w) for w in parts[0]]) + len(parts[0]))
        parts.append(words[midword:])
        partsizes.append(sum([len(w) for w in parts[1]]) + len(parts[1]))
    else:
        parts.append(words)
        partsizes.append(sum([len(w) for w in parts[0]]) + len(parts[0]))

    while max(partsizes) > allow_length:
        for widx in range(len(parts)):
            if partsizes[widx] > allow_length:
                if widx > 0 and partsizes[widx - 1] < allow_length - len(parts[widx][0]):
                    # move to previous part
                    move_text = parts[widx].pop(0)
                    parts[widx - 1].append(move_text)
                    partsizes[widx - 1] += len(move_text) + 1
                    partsizes[widx] -= len(move_text) + 1
                else:
                    # move to next part
                    if len(parts) == widx + 1:
                        parts.append([])
                        partsizes.append(0)
                    move_text = parts[widx].pop()
                    parts[widx + 1].insert(0, move_text)
                    partsizes[widx + 1] += len(move_text) + 1
                    partsizes[widx] -= len(move_text) + 1
    return [" ".join(p) for p in parts]

def text_image_usage():
    text_to_show = ("I live daily with the realization that people I thought were good people are really hateful dirtbags.",
             "It gets easier with time.")
    arranged = arrange_text(text_to_show)
    img = render_text(font_path=None, lines=arranged)

    img.show()
    # img.save('render_test.png')

if __name__ == "__main__":
    text_image_usage()
