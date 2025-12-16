from enum import Enum
import sys

if sys.version_info >= (3, 11):
  from enum import StrEnum


class FileExtension(StrEnum):
  PDF = '.pdf'
  TXT = '.txt'
  DOCX = '.docx'
  CSV = '.csv'
  JSON = '.json'
  PPTX = '.pptx'


class EncodingType(StrEnum):
  UTF8 = 'utf-8'
  UTF8_SIG = 'utf-8-sig'
  LATIN1 = 'latin-1'
  CP1252 = 'cp1252'


class TextSeparator(StrEnum):
  DOUBLE_NEWLINE = "\n\n"
  NEWLINE = "\n"
  PERIOD = "."
  SPACE = " "


class ParsingConstants(StrEnum):
  HEADERS_PREFIX = "Headers: "
  COLUMN_SEPARATOR = " | "
  KEY_VALUE_SEPARATOR = ": "
  OBJECT_SEPARATOR = "."
  ITEM_PREFIX = "item_"
