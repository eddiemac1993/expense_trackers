from django import template

register = template.Library()

ONES = (
    "Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
    "Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen"
).split()

TENS = "Zero Ten Twenty Thirty Forty Fifty Sixty Seventy Eighty Ninety".split()

def num_to_words(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ('' if n % 10 == 0 else ' ' + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + ' Hundred' + ('' if n % 100 == 0 else ' ' + num_to_words(n % 100))
    if n < 1_000_000:
        return num_to_words(n // 1000) + ' Thousand' + ('' if n % 1000 == 0 else ' ' + num_to_words(n % 1000))
    return str(n)

@register.filter
def amount_in_words(value):
    try:
        value = float(value)
        kwacha = int(value)
        ngwee = int(round((value - kwacha) * 100))

        words = f"{num_to_words(kwacha)} Kwacha"
        if ngwee > 0:
            words += f" And {num_to_words(ngwee)} Ngwee"
        else:
            words += " Only"

        return words
    except Exception:
        return ""
