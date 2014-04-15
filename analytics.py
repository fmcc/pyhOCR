from collections import Counter

def get_stats(page):
    labels = Counter()
    for line in page.children:
        labels.update([word.label for word in line.children])
    total_lines = len(page.children)
    total_words = sum(labels.values())
    total_area = sum([word.height*word.width for line in page.children for word in line.children])
    if total_words:
        greek_ratio = 100 * float(labels['GREEK'])/float(total_words) 
        latin_ratio = 100 * float(labels['LATIN'])/float(total_words) 
    else:
        greek_ratio = 0
        latin_ratio = 0
    widths = [l.width for l in page.children]
    if widths:
        avg_line_width = sum(widths)/len(widths)
    else:
        avg_line_width = 0 

    heights = [l.height for l in page.children]
    if heights:
        avg_line_height = sum(heights)/len(heights)
    else:
        avg_line_height = 0 

    return [total_lines, total_words, greek_ratio, latin_ratio, avg_line_width, avg_line_height, total_area]
