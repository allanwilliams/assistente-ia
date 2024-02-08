from django.forms import Select
from django.utils.html import format_html

class SelectWidget(Select): # pragma: no cover
    def __init__(self, *args, **kwargs):
        self._disabled_choices = []
        super(SelectWidget, self).__init__(*args, **kwargs)

    @property
    def disabled_choices(self):
        return self._disabled_choices

    @disabled_choices.setter
    def disabled_choices(self, other):
        self._disabled_choices = other

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option_dict = super(SelectWidget, self).create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if value in self.disabled_choices:
            option_dict['attrs']['disabled'] = 'disabled'
        return option_dict


def label_tooltip(label, help_text, position='top'): # pragma: no cover
    """Função para customizar uma field label colocando um icone de ajuda e um tooltip com help text do lado da label
        Posições: bottom, top, left, right [default=top]"""
    return format_html("<span>{label} <a href='#' data-toggle='tooltip' data-placement='{position}' title='' data-original-title='{help_text}'><i class='fa fa-fw fa-question-circle'></i></a></span>",
        help_text=help_text,
        position=position,
        label=label)