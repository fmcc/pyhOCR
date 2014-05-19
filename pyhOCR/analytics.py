from collections import Counter

def generate_page_stats(page):
    stats = {}
    stats.update(page_number(page))
    stats.update(num_words(page))
    stats.update(num_lines(page))
    stats.update(avg_line_width(page))
    stats.update(avg_line_height(page))
    stats.update(word_ratios(page))
    # We shouldn't need this as a Dict, return as an alphabetically sorted list of tuples.
    return sorted(stats.items(), key=lambda item: item[0])

def page_number(page):
    """ Utility method to include page number as a statistic """
    return {'PAGE_NUMBER': page.number }

def num_words(page):
    """ Returns the number of words on a page """
    return {'NUM_WORDS': len([word for line in page.children for word in line.children])}

def num_lines(page):
    """ Returns the number of lines on a page """
    return {'NUM_LINES': len(page.children)}

def avg_line_width(page):
    """ Returns the average width of a line on the page """
    widths = [l.width for l in page.children]
    if widths:
        avg_line_width = sum(widths)/len(widths)
    else:
        avg_line_width = 0 
    return {'LINE_WIDTH': avg_line_width}

def avg_line_height(page):
    """ Returns the average line height on the page """
    heights = [l.height for l in page.children]
    if heights:
        avg_line_height = sum(heights)/len(heights)
    else:
        avg_line_height = 0
    return {'LINE_HEIGHT': avg_line_height}

def word_ratios(page, word_types=['GREEK','LATIN']):
    """ Returns ratios of word types on page as a dict with the type as keys
        defaults to Greek and Latin, but can take a list of types as an argument."""
    labels = Counter()
    for line in page.children:
        labels.update([word.label for word in line.children])
    total_words = sum(labels.values())
    ratios = {t:0 for t in word_types}
    if total_words:
        for t in word_types:
            ratios[t] = 100 * float(labels[t])/float(total_words) 
    return ratios
