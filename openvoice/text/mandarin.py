import os
import sys
import re
from pypinyin import lazy_pinyin, BOPOMOFO
import jieba
import cn2an
import logging


# List of (Latin alphabet, bopomofo) pairs:
_latin_to_bopomofo = [(re.compile('%s' % x[0], re.IGNORECASE), x[1]) for x in [
    ('a', 'ㄟˉ'),
    ('b', 'ㄅㄧˋ'),
    ('c', 'ㄙㄧˉ'),
    ('d', 'ㄉㄧˋ'),
    ('e', 'ㄧˋ'),
    ('f', 'ㄝˊㄈㄨˋ'),
    ('g', 'ㄐㄧˋ'),
    ('h', 'ㄝˇㄑㄩˋ'),
    ('i', 'ㄞˋ'),
    ('j', 'ㄐㄟˋ'),
    ('k', 'ㄎㄟˋ'),
    ('l', 'ㄝˊㄛˋ'),
    ('m', 'ㄝˊㄇㄨˋ'),
    ('n', 'ㄣˉ'),
    ('o', 'ㄡˉ'),
    ('p', 'ㄆㄧˉ'),
    ('q', 'ㄎㄧㄡˉ'),
    ('r', 'ㄚˋ'),
    ('s', 'ㄝˊㄙˋ'),
    ('t', 'ㄊㄧˋ'),
    ('u', 'ㄧㄡˉ'),
    ('v', 'ㄨㄧˉ'),
    ('w', 'ㄉㄚˋㄅㄨˋㄌㄧㄡˋ'),
    ('x', 'ㄝˉㄎㄨˋㄙˋ'),
    ('y', 'ㄨㄞˋ'),
    ('z', 'ㄗㄟˋ')
]]

# List of (bopomofo, romaji) pairs:
_bopomofo_to_romaji = [(re.compile('%s' % x[0]), x[1]) for x in [
    ('ㄅㄛ', 'p⁼wo'),
    ('ㄆㄛ', 'pʰwo'),
    ('ㄇㄛ', 'mwo'),
    ('ㄈㄛ', 'fwo'),
    ('ㄅ', 'p⁼'),
    ('ㄆ', 'pʰ'),
    ('ㄇ', 'm'),
    ('ㄈ', 'f'),
    ('ㄉ', 't⁼'),
    ('ㄊ', 'tʰ'),
    ('ㄋ', 'n'),
    ('ㄌ', 'l'),
    ('ㄍ', 'k⁼'),
    ('ㄎ', 'kʰ'),
    ('ㄏ', 'h'),
    ('ㄐ', 'ʧ⁼'),
    ('ㄑ', 'ʧʰ'),
    ('ㄒ', 'ʃ'),
    ('ㄓ', 'ʦ`⁼'),
    ('ㄔ', 'ʦ`ʰ'),
    ('ㄕ', 's`'),
    ('ㄖ', 'ɹ`'),
    ('ㄗ', 'ʦ⁼'),
    ('ㄘ', 'ʦʰ'),
    ('ㄙ', 's'),
    ('ㄚ', 'a'),
    ('ㄛ', 'o'),
    ('ㄜ', 'ə'),
    ('ㄝ', 'e'),
    ('ㄞ', 'ai'),
    ('ㄟ', 'ei'),
    ('ㄠ', 'au'),
    ('ㄡ', 'ou'),
    ('ㄧㄢ', 'yeNN'),
    ('ㄢ', 'aNN'),
    ('ㄧㄣ', 'iNN'),
    ('ㄣ', 'əNN'),
    ('ㄤ', 'aNg'),
    ('ㄧㄥ', 'iNg'),
    ('ㄨㄥ', 'uNg'),
    ('ㄩㄥ', 'yuNg'),
    ('ㄥ', 'əNg'),
    ('ㄦ', 'əɻ'),
    ('ㄧ', 'i'),
    ('ㄨ', 'u'),
    ('ㄩ', 'ɥ'),
    ('ˉ', '→'),
    ('ˊ', '↑'),
    ('ˇ', '↓↑'),
    ('ˋ', '↓'),
    ('˙', ''),
    ('，', ','),
    ('。', '.'),
    ('！', '!'),
    ('？', '?'),
    ('—', '-')
]]

# List of (romaji, ipa) pairs:
_romaji_to_ipa = [(re.compile('%s' % x[0], re.IGNORECASE), x[1]) for x in [
    ('ʃy', 'ʃ'),
    ('ʧʰy', 'ʧʰ'),
    ('ʧ⁼y', 'ʧ⁼'),
    ('NN', 'n'),
    ('Ng', 'ŋ'),
    ('y', 'j'),
    ('h', 'x')
]]

# List of (bopomofo, ipa) pairs:
_bopomofo_to_ipa = [(re.compile('%s' % x[0]), x[1]) for x in [
    ('ㄅㄛ', 'p⁼wo'),
    ('ㄆㄛ', 'pʰwo'),
    ('ㄇㄛ', 'mwo'),
    ('ㄈㄛ', 'fwo'),
    ('ㄅ', 'p⁼'),
    ('ㄆ', 'pʰ'),
    ('ㄇ', 'm'),
    ('ㄈ', 'f'),
    ('ㄉ', 't⁼'),
    ('ㄊ', 'tʰ'),
    ('ㄋ', 'n'),
    ('ㄌ', 'l'),
    ('ㄍ', 'k⁼'),
    ('ㄎ', 'kʰ'),
    ('ㄏ', 'x'),
    ('ㄐ', 'tʃ⁼'),
    ('ㄑ', 'tʃʰ'),
    ('ㄒ', 'ʃ'),
    ('ㄓ', 'ts`⁼'),
    ('ㄔ', 'ts`ʰ'),
    ('ㄕ', 's`'),
    ('ㄖ', 'ɹ`'),
    ('ㄗ', 'ts⁼'),
    ('ㄘ', 'tsʰ'),
    ('ㄙ', 's'),
    ('ㄚ', 'a'),
    ('ㄛ', 'o'),
    ('ㄜ', 'ə'),
    ('ㄝ', 'ɛ'),
    ('ㄞ', 'aɪ'),
    ('ㄟ', 'eɪ'),
    ('ㄠ', 'ɑʊ'),
    ('ㄡ', 'oʊ'),
    ('ㄧㄢ', 'jɛn'),
    ('ㄩㄢ', 'ɥæn'),
    ('ㄢ', 'an'),
    ('ㄧㄣ', 'in'),
    ('ㄩㄣ', 'ɥn'),
    ('ㄣ', 'ən'),
    ('ㄤ', 'ɑŋ'),
    ('ㄧㄥ', 'iŋ'),
    ('ㄨㄥ', 'ʊŋ'),
    ('ㄩㄥ', 'jʊŋ'),
    ('ㄥ', 'əŋ'),
    ('ㄦ', 'əɻ'),
    ('ㄧ', 'i'),
    ('ㄨ', 'u'),
    ('ㄩ', 'ɥ'),
    ('ˉ', '→'),
    ('ˊ', '↑'),
    ('ˇ', '↓↑'),
    ('ˋ', '↓'),
    ('˙', ''),
    ('，', ','),
    ('。', '.'),
    ('！', '!'),
    ('？', '?'),
    ('—', '-')
]]

# List of (bopomofo, ipa2) pairs:
_bopomofo_to_ipa2 = [(re.compile('%s' % x[0]), x[1]) for x in [
    ('ㄅㄛ', 'pwo'),
    ('ㄆㄛ', 'pʰwo'),
    ('ㄇㄛ', 'mwo'),
    ('ㄈㄛ', 'fwo'),
    ('ㄅ', 'p'),
    ('ㄆ', 'pʰ'),
    ('ㄇ', 'm'),
    ('ㄈ', 'f'),
    ('ㄉ', 't'),
    ('ㄊ', 'tʰ'),
    ('ㄋ', 'n'),
    ('ㄌ', 'l'),
    ('ㄍ', 'k'),
    ('ㄎ', 'kʰ'),
    ('ㄏ', 'h'),
    ('ㄐ', 'tɕ'),
    ('ㄑ', 'tɕʰ'),
    ('ㄒ', 'ɕ'),
    ('ㄓ', 'tʂ'),
    ('ㄔ', 'tʂʰ'),
    ('ㄕ', 'ʂ'),
    ('ㄖ', 'ɻ'),
    ('ㄗ', 'ts'),
    ('ㄘ', 'tsʰ'),
    ('ㄙ', 's'),
    ('ㄚ', 'a'),
    ('ㄛ', 'o'),
    ('ㄜ', 'ɤ'),
    ('ㄝ', 'ɛ'),
    ('ㄞ', 'aɪ'),
    ('ㄟ', 'eɪ'),
    ('ㄠ', 'ɑʊ'),
    ('ㄡ', 'oʊ'),
    ('ㄧㄢ', 'jɛn'),
    ('ㄩㄢ', 'yæn'),
    ('ㄢ', 'an'),
    ('ㄧㄣ', 'in'),
    ('ㄩㄣ', 'yn'),
    ('ㄣ', 'ən'),
    ('ㄤ', 'ɑŋ'),
    ('ㄧㄥ', 'iŋ'),
    ('ㄨㄥ', 'ʊŋ'),
    ('ㄩㄥ', 'jʊŋ'),
    ('ㄥ', 'ɤŋ'),
    ('ㄦ', 'əɻ'),
    ('ㄧ', 'i'),
    ('ㄨ', 'u'),
    ('ㄩ', 'y'),
    ('ˉ', '˥'),
    ('ˊ', '˧˥'),
    ('ˇ', '˨˩˦'),
    ('ˋ', '˥˩'),
    ('˙', ''),
    ('，', ','),
    ('。', '.'),
    ('！', '!'),
    ('？', '?'),
    ('—', '-')
]]


def number_to_chinese(text):
    numbers = re.findall(r'\d+(?:\.?\d+)?', text)
    for number in numbers:
        text = text.replace(number, cn2an.an2cn(number), 1)
    return text

'''
注音符号（zhù yīn fú hào，ㄓㄨˋ ㄧㄣ ㄈㄨˊ ㄏㄠˋ）另称“bopomofo”，是现代汉语的标音系统之一，除了可以标注普通话，也可以用来标注其他汉语方言，例如闽南话。
注音创立于二十世纪初（中华民国时期），虽然现今已大致被拼音取代，但在字典中还能看到。
截至目前，注音依然是台湾的首要拼写系统。
'''
def chinese_to_bopomofo(text):
    text = text.replace('、', '，').replace('；', '，').replace('：', '，')
    words = jieba.lcut(text, cut_all=False)    # 对中文字符串进行分词. 参考：https://github.com/fxsjy/jieba
    text = ''
    for word in words:
        bopomofos = lazy_pinyin(word, BOPOMOFO)
        if not re.search('[\u4e00-\u9fff]', word):
            text += word
            continue
        for i in range(len(bopomofos)):
            bopomofos[i] = re.sub(r'([\u3105-\u3129])$', r'\1ˉ', bopomofos[i])
        if text != '':
            text += ' '
        text += ''.join(bopomofos)
    return text


def latin_to_bopomofo(text):
    for regex, replacement in _latin_to_bopomofo:
        text = re.sub(regex, replacement, text)
    return text


def bopomofo_to_romaji(text):
    for regex, replacement in _bopomofo_to_romaji:
        text = re.sub(regex, replacement, text)
    return text


def bopomofo_to_ipa(text):
    for regex, replacement in _bopomofo_to_ipa:
        text = re.sub(regex, replacement, text)
    return text


def bopomofo_to_ipa2(text):
    for regex, replacement in _bopomofo_to_ipa2:
        text = re.sub(regex, replacement, text)
    return text


def chinese_to_romaji(text):
    text = number_to_chinese(text)
    text = chinese_to_bopomofo(text)
    text = latin_to_bopomofo(text)
    text = bopomofo_to_romaji(text)
    text = re.sub('i([aoe])', r'y\1', text)
    text = re.sub('u([aoəe])', r'w\1', text)
    text = re.sub('([ʦsɹ]`[⁼ʰ]?)([→↓↑ ]+|$)',
                  r'\1ɹ`\2', text).replace('ɻ', 'ɹ`')
    text = re.sub('([ʦs][⁼ʰ]?)([→↓↑ ]+|$)', r'\1ɹ\2', text)
    return text


def chinese_to_lazy_ipa(text):
    text = chinese_to_romaji(text)
    for regex, replacement in _romaji_to_ipa:
        text = re.sub(regex, replacement, text)
    return text


def chinese_to_ipa(text):
    text = number_to_chinese(text)
    text = chinese_to_bopomofo(text)
    text = latin_to_bopomofo(text)
    text = bopomofo_to_ipa(text)        # 现代标准汉语（普通话、国语、华语）发音的方式，国际音标。
    text = re.sub('i([aoe])', r'j\1', text)
    text = re.sub('u([aoəe])', r'w\1', text)
    text = re.sub('([sɹ]`[⁼ʰ]?)([→↓↑ ]+|$)',
                  r'\1ɹ`\2', text).replace('ɻ', 'ɹ`')
    text = re.sub('([s][⁼ʰ]?)([→↓↑ ]+|$)', r'\1ɹ\2', text)
    return text


def chinese_to_ipa2(text):
    text = number_to_chinese(text)
    text = chinese_to_bopomofo(text)
    text = latin_to_bopomofo(text)
    text = bopomofo_to_ipa2(text)
    text = re.sub(r'i([aoe])', r'j\1', text)
    text = re.sub(r'u([aoəe])', r'w\1', text)
    text = re.sub(r'([ʂɹ]ʰ?)([˩˨˧˦˥ ]+|$)', r'\1ʅ\2', text)
    text = re.sub(r'(sʰ?)([˩˨˧˦˥ ]+|$)', r'\1ɿ\2', text)
    return text
