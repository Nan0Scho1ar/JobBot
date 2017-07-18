from helpers import Const


class HTMLConstants(Const):

    class TagType(Const):
        DIV = 'div'
        SPAN = 'span'
        INPUT = 'input'
        TEXTAREA = 'textarea'
        SELECT = 'select'
        H2 = 'h2'
        ANCHOR = 'a'

    class Attributes(Const):
        HREF = 'href'
        TYPE = 'type'
        ID = 'id'
        INNER_TEXT = 'innerText'
        NAME = 'name'
        FOR = 'for'

    class InputTypes(Const):
        RADIO = 'radio'
        TEXT = 'text'
        EMAIL = 'email'
        FILE = 'file'
        TEXTAREA = 'textarea'
        HIDDEN = 'hidden'
